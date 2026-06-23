def list_microphones(sr_module):
    return sr_module.Microphone.list_microphone_names()


def print_microphones(sr_module):
    for index, name in enumerate(list_microphones(sr_module)):
        print(f"{index}: {name}")


def create_microphone(sr_module, device_index=None):
    return sr_module.Microphone(device_index=device_index)
