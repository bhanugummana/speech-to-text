import unittest
import io
import queue
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from speechcli.dictation import DictationOptions, DictationState

from main import (
    MAX_SHUTDOWN_SETTLE_SECONDS,
    MIN_SHUTDOWN_SETTLE_SECONDS,
    TRANSCRIPT_CONFIDENCE_MARGIN,
    drain_pending_audio,
    handle_unclear_audio,
    recognize_audio,
    save_unclear_audio,
    select_best_transcript,
    shutdown_settle_timeout,
    wait_for_listener_to_settle,
)


class FakeRecognizer:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def recognize_google(self, audio, language=None, show_all=False):
        self.calls.append({
            "audio": audio,
            "language": language,
            "show_all": show_all,
        })
        return self.responses.pop(0)


class FakeAudio:
    def __init__(self, data=b"wav-data"):
        self.data = data

    def get_wav_data(self):
        return self.data


class FakeThread:
    def __init__(self, alive=True):
        self.alive = alive
        self.join_timeout = None

    def is_alive(self):
        return self.alive

    def join(self, timeout=None):
        self.join_timeout = timeout


class RecognitionTest(unittest.TestCase):
    def test_select_best_transcript_uses_highest_confidence(self):
        response = {
            "alternative": [
                {"transcript": "hello word", "confidence": 0.72},
                {"transcript": "hello world", "confidence": 0.91},
            ],
        }

        self.assertEqual(select_best_transcript(response), "hello world")

    def test_select_best_transcript_prefers_more_words_when_confidence_ties(self):
        response = {
            "alternative": [
                {"transcript": "open settings", "confidence": 0.84},
                {"transcript": "open the settings window", "confidence": 0.84},
            ],
        }

        self.assertEqual(select_best_transcript(response), "open the settings window")

    def test_select_best_transcript_prefers_more_words_near_best_confidence(self):
        response = {
            "alternative": [
                {"transcript": "please open settings", "confidence": 0.91},
                {
                    "transcript": "please open the settings window",
                    "confidence": 0.91 - TRANSCRIPT_CONFIDENCE_MARGIN,
                },
            ],
        }

        self.assertEqual(
            select_best_transcript(response),
            "please open the settings window",
        )

    def test_select_best_transcript_rejects_much_lower_confidence_longer_text(self):
        response = {
            "alternative": [
                {"transcript": "open settings", "confidence": 0.92},
                {
                    "transcript": "open settings with unrelated extra words",
                    "confidence": 0.5,
                },
            ],
        }

        self.assertEqual(select_best_transcript(response), "open settings")

    def test_select_best_transcript_handles_empty_response(self):
        self.assertIsNone(select_best_transcript({}))
        self.assertIsNone(select_best_transcript({"alternative": []}))
        self.assertIsNone(select_best_transcript([]))

    def test_recognize_audio_requests_all_alternatives(self):
        recognizer = FakeRecognizer([
            {"alternative": [{"transcript": "captured every word"}]},
        ])

        result = recognize_audio(recognizer, "audio", "en-US", None, False)

        self.assertEqual(result, "captured every word")
        self.assertEqual(recognizer.calls[0]["audio"], "audio")
        self.assertEqual(recognizer.calls[0]["language"], "en-US")
        self.assertTrue(recognizer.calls[0]["show_all"])

    def test_recognize_audio_retries_empty_recognition_once(self):
        recognizer = FakeRecognizer([
            {},
            {"alternative": [{"transcript": "recovered words"}]},
        ])

        with patch("main.time.sleep"):
            result = recognize_audio(recognizer, "audio", "en-US", None, False)

        self.assertEqual(result, "recovered words")
        self.assertEqual(len(recognizer.calls), 2)

    def test_recognize_audio_returns_none_after_repeated_empty_recognition(self):
        recognizer = FakeRecognizer([{}, {}])

        with patch("main.time.sleep"):
            result = recognize_audio(recognizer, "audio", "en-US", None, False)

        self.assertIsNone(result)
        self.assertEqual(len(recognizer.calls), 2)

    def test_recognize_audio_does_not_archive_unclear_audio_by_default(self):
        recognizer = FakeRecognizer([{}, {}])

        with patch("main.time.sleep"), patch("main.save_unclear_audio") as save_audio:
            result = recognize_audio(
                recognizer,
                FakeAudio(),
                "en-US",
                None,
                False,
            )

        self.assertIsNone(result)
        save_audio.assert_not_called()

    def test_recognize_audio_archives_unclear_audio_when_enabled(self):
        recognizer = FakeRecognizer([{}, {}])
        audio = FakeAudio()

        with patch("main.time.sleep"), patch("main.save_unclear_audio", return_value="/tmp/chunk.wav") as save_audio:
            result = recognize_audio(
                recognizer,
                audio,
                "en-US",
                None,
                False,
                archive_unclear_audio=True,
            )

        self.assertIsNone(result)
        save_audio.assert_called_once_with(audio, "empty-recognition")

    def test_handle_unclear_audio_shows_archived_status_when_file_is_saved(self):
        with patch("main.save_unclear_audio", return_value="/tmp/chunk.wav"):
            with patch("main.update_overlay") as update_overlay:
                result = handle_unclear_audio(
                    FakeAudio(),
                    "empty-recognition",
                    "overlay",
                    False,
                    archive_unclear_audio=True,
                )

        self.assertIsNone(result)
        update_overlay.assert_called_once_with("overlay", "status", "Chunk archived")

    def test_handle_unclear_audio_shows_unclear_status_without_archive(self):
        with patch("main.save_unclear_audio") as save_audio:
            with patch("main.update_overlay") as update_overlay:
                result = handle_unclear_audio(
                    FakeAudio(),
                    "empty-recognition",
                    "overlay",
                    False,
                    archive_unclear_audio=False,
                )

        self.assertIsNone(result)
        save_audio.assert_not_called()
        update_overlay.assert_called_once_with("overlay", "status", "Chunk unclear")

    def test_save_unclear_audio_writes_wav_data(self):
        with patch("main.time.strftime", return_value="20260706-120000"):
            with patch("main.time.time_ns", return_value=1234):
                with patch("main.os.getpid", return_value=42):
                    with patch("main.threading.get_ident", return_value=7):
                        with self.subTest("writes file"):
                            import tempfile
                            with tempfile.TemporaryDirectory() as directory:
                                path = save_unclear_audio(
                                    FakeAudio(b"audio-bytes"),
                                    "empty recognition",
                                    directory,
                                )

                                with open(path, "rb") as f:
                                    self.assertEqual(f.read(), b"audio-bytes")
                                self.assertTrue(path.endswith("empty-recognition.wav"))

    def test_drain_pending_audio_transcribes_queued_chunks_after_stop(self):
        pending_queue = queue.Queue()
        pending_queue.put("audio-one")
        pending_queue.put("audio-two")
        recognizer = FakeRecognizer([
            {"alternative": [{"transcript": "first queued words"}]},
            {"alternative": [{"transcript": "second queued words"}]},
        ])
        state = DictationState()
        options = SimpleNamespace(
            language="en-US",
            should_copy=False,
            should_output=False,
            should_type=False,
            verbose=False,
        )

        with patch("main.running", False), redirect_stdout(io.StringIO()):
            drained = drain_pending_audio(
                pending_queue,
                recognizer,
                state,
                DictationOptions(),
                options,
                None,
            )

        self.assertEqual(drained, 2)
        self.assertTrue(pending_queue.empty())
        self.assertEqual(state.cumulative_text, "first queued words second queued words")
        self.assertEqual(len(recognizer.calls), 2)

    def test_shutdown_settle_timeout_tracks_pause_threshold_with_bounds(self):
        self.assertEqual(
            shutdown_settle_timeout(SimpleNamespace(
                pause_threshold=0.0,
                phrase_time_limit=0.0,
            )),
            MIN_SHUTDOWN_SETTLE_SECONDS,
        )
        self.assertEqual(
            shutdown_settle_timeout(SimpleNamespace(
                pause_threshold=1.0,
                phrase_time_limit=3.0,
            )),
            3.0,
        )
        self.assertEqual(
            shutdown_settle_timeout(SimpleNamespace(
                pause_threshold=1.0,
                phrase_time_limit=12.0,
            )),
            MAX_SHUTDOWN_SETTLE_SECONDS,
        )

    def test_wait_for_listener_to_settle_joins_alive_thread_with_bounded_timeout(self):
        listener_thread = FakeThread()

        wait_for_listener_to_settle(
            listener_thread,
            SimpleNamespace(pause_threshold=1.0, phrase_time_limit=3.0),
        )

        self.assertEqual(listener_thread.join_timeout, 3.0)

    def test_wait_for_listener_to_settle_skips_finished_thread(self):
        listener_thread = FakeThread(alive=False)

        wait_for_listener_to_settle(
            listener_thread,
            SimpleNamespace(pause_threshold=1.0, phrase_time_limit=3.0),
        )

        self.assertIsNone(listener_thread.join_timeout)


if __name__ == "__main__":
    unittest.main()
