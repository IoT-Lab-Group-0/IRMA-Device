import time

import voice_command

def start(barcode, wake, speaker, db):
    try:
        while True:
            # Check sensor flags
            if wake():
                cmd, item = voice_command.get_command()
                if cmd == "add":
                    db.add_item(item)
                    speaker.say("Adding " + item.name)
                elif cmd == "remove":
                    db.remove_item(item)
                    speaker.say("Removing " + item.name)
                else:
                    pass

            if barcode() and barcode.is_connected():
                item = barcode.get_item()
                db.add_item(item)
                speaker.say("Adding " + item.name)

            time.sleep(0.2)

    except Exception as e:
        print('Exception: ', e)
        barcode.close()
        wake.close()
        exit(1)

    finally:
        barcode.close()
        wake.close()
        exit(0)
