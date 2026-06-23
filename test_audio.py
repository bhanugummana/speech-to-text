import unittest

from speechcli.audio import create_microphone, list_microphones


class FakeMicrophone:
    last_device_index = None

    def __init__(self, device_index=None):
        FakeMicrophone.last_device_index = device_index

    @staticmethod
    def list_microphone_names():
        return ["Default", "USB Mic"]


class FakeSpeechRecognition:
    Microphone = FakeMicrophone


class AudioTest(unittest.TestCase):
    def test_list_microphones_returns_names(self):
        self.assertEqual(list_microphones(FakeSpeechRecognition), ["Default", "USB Mic"])

    def test_create_microphone_uses_device_index(self):
        create_microphone(FakeSpeechRecognition, 1)

        self.assertEqual(FakeMicrophone.last_device_index, 1)


if __name__ == "__main__":
    unittest.main()
