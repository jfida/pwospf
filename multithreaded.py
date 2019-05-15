import threading
# import zmq
import time


def child_stuff(num):
    while True:
        print(num)
        time.sleep(0.5)


def main():
    thread = threading.Thread(target=childStuff, args=[1]).start()
    thread2 = threading.Thread(target=childStuff, args=[2]).start()

    # while True:
    #     print("he")
    #     time.sleep(0.5)


if __name__ == "__main__":
    main()
