import uuid

import serial.tools.list_ports
import datetime
import random

curr_user = "default"
user_data = {}

has_played_before = False

def createFile():
    try:
        with open('data.ini', 'x') as f:
            init()
    except FileExistsError:
        print("File already exists")


def init():
    timestamp = "timestamp=" + str(datetime.datetime.now())
    with open('data.ini', 'w') as f:
        f.write("[init]\n" + timestamp + "\n")

def doesIdAlreadyExist(id):
    with open('data.ini', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith(f"id={id}"):
                return True
    return False


def registerUser(username, phone):
    global curr_user
    curr_user = username
    global has_played_before
    has_played_before = False
    id = uuid.uuid4()
    if doesIdAlreadyExist(id):
        print("ID already exists, generating new ID")
        print(id)
        print("waaaaaaaaaaaiiiit!!!!!!!!!!!")
        registerUser(username, phone)
    user_data[curr_user] = {
        "id": id,
        "timestamp": str(datetime.datetime.now()),
        "name": username,
        "phone": phone,
        "run_count": 1
    }
    with open('data.ini', 'a') as f:
        f.write(f"[user.{user_data[curr_user]['id']}]\n")
        f.write(f"id={user_data[curr_user]['id']}\n")
        f.write(f"timestamp={user_data[curr_user]['timestamp']}\n")
        f.write(f"name={user_data[curr_user]['name']}\n")
        f.write(f"phone={user_data[curr_user]['phone']}\n")
        f.write(f"run_count={user_data[curr_user]['run_count']}\n")

def selectUser(user_id):
    with open('data.ini', 'r') as f:
        lines = f.readlines()

    # Find the index of the "[user.<id>.finished]" line
    finished_line_index = None
    found_id = False
    tmp_phone = None
    tmp_name = None
    tmp_id = None
    tmp_run_count = None
    for i, line in enumerate(lines):
        if found_id:
            if line.startswith("run_count"):
                tmp_run_count = int(line.split("=")[1].strip()) + 1
                lines[i] = f"run_count={tmp_run_count}\n"

            if line.startswith("id"):
                tmp_id = line.split("=")[1].strip()
            if line.startswith("name"):
                tmp_name = line.split("=")[1].strip()
            if line.startswith("phone"):
                tmp_phone = line.split("=")[1].strip()
            if tmp_phone != None and tmp_name != None and tmp_id != None and tmp_run_count != None:
                global user_data
                global curr_user
                curr_user = tmp_id
                user_data[tmp_id] = {
                    "id": tmp_id,
                    "timestamp": str(datetime.datetime.now()),
                    "name": tmp_name,
                    "phone": tmp_phone,
                    "run_count": tmp_run_count
                }

                print(user_data)
            if i == finished_line_index + 5:
                break
        if line.strip() == f"[user.{user_id}]":
            finished_line_index = i
            found_id = True
    with open('data.ini', 'w') as f:
        f.writelines(lines)

    print(f"Updated run_count for user {user_id} to {tmp_run_count}.")


def login():
    print("--------------")
    print("--------------")
    global has_played_before
    has_played_before = True
    with open('data.ini', 'r') as f:
        lines=f.readlines()
        previous_lines = [None, None, None]  # A list to store the last three lines read

        for line in lines:
            # If the line starts with "name", print the three previous lines and the current line
            if line.startswith("phone"):
                if previous_lines[0] is not None:
                    print(previous_lines[0].strip())  # Three lines above
                if previous_lines[1] is not None:
                    print(previous_lines[1].strip())  # Two lines above
                if previous_lines[2] is not None:
                    print(previous_lines[2].strip())  # One line above
                print(line.strip())  # Current line starting with "name"
                print("--------------")

            # Update previous_lines to store the last three lines read
            previous_lines[0] = previous_lines[1]
            previous_lines[1] = previous_lines[2]
            previous_lines[2] = line
    print("Paste the ID of the user you want to select")
    selectUser(input("Enter ID: "))


def selectPort():
    ports=serial.tools.list_ports.comports()
    serialInst =serial.Serial()
    portList =[]

    for port in ports:
        portList.append(str(port))
        print(str(port))

    val=input("Select Port: COM")

    for x in range(len(portList)):
        if portList[x].startswith("COM" + str(val)):
            portVar="COM" + str(val)
            print(f"Port selected: {portList[x]}")

    serialInst.baudrate =115200
    serialInst.port =portVar
    serialInst.open()
    serialInst.write("rq".encode('utf-8'))
    logGameData(serialInst)


def logGameData(serialInst):
    with open('data.ini', 'a') as f:
        if not has_played_before:
            f.write(f"[user.{user_data[curr_user]['id']}.data]\n")
            while True:
                if serialInst.in_waiting:
                    packet = serialInst.readline().decode('utf-8').strip()
                    f.write(packet + "\n")

                    # Check for level 14 completion to end the session
                    if packet.startswith("lvl;14"):
                        print("Level 14 reached!")
                        f.write(f"[user.{user_data[curr_user]['id']}.finished]\n")
                        break
                    print(packet)
        if has_played_before:
            with open('data.ini', 'r') as f:
                lines = f.readlines()

            # Find the index of the "[user.<id>.finished]" line
            finished_line_index = None
            for i, line in enumerate(lines):
                if line.strip() == f"[user.{user_data[curr_user]['id']}.finished]":
                    finished_line_index = i
                    break

            if finished_line_index is None:
                print(f"No finished section found for user {user_data[curr_user]['id']}.")
                return
            # Prepare to insert data above the finished marker
            insert_index = finished_line_index  # Where we’ll start writing game data
            data_lines = ["[user." + str(user_data[curr_user]['id']) + ".data]\n"]


            while True:
                if serialInst.in_waiting:
                    packet = serialInst.readline().decode('utf-8').strip()
                    data_lines.append(packet + "\n")  # Collect data lines for insertion

                    # Check for level 14 completion to end the session
                    if packet.startswith("lvl;14"):
                        print("Level 14 reached!")
                        break
                    print(packet)

            # Insert the collected data above the finished marker
            lines[insert_index:insert_index] = data_lines

            # Write the updated content back to the file
            with open('data.ini', 'w') as f:
                f.writelines(lines)

            print(f"Data successfully written above the [user.{user_data[curr_user]['id']}.finished] line.")


def summarizeRun(user_id):
    with open('data.ini', 'r') as f:
        lines = f.readlines()

    # Find the index of the "[user.<id>.finished]" line
    finished_line_index = None
    for i, line in enumerate(lines):
        if line.strip() == f"[user.{user_id}.finished]":
            finished_line_index = i
            break

    if finished_line_index is None:
        print(f"No finished section found for user {user_id}.")
        return

    # Scan upwards for lvlt, dth, and rst values
    last_lvlt = None
    last_dth = None
    last_rst = None

    for line in reversed(lines[:finished_line_index]):
        if line.startswith("lvlt;") and last_lvlt is None:
            last_lvlt = line.split(";")[1].strip()
        elif line.startswith("dth;") and last_dth is None:
            last_dth = line.split(";")[1].strip()
        elif line.startswith("rst;") and last_rst is None:
            last_rst = line.split(";")[1].strip()

        # Stop once we have all three values
        if last_lvlt is not None and last_dth is not None and last_rst is not None:
            break

    # Create the new run section with the extracted values
    new_run_section = (
        f"[user.{user_id}.run.{user_data[curr_user]['run_count']}]\n"
        f"time={last_lvlt}\n"
        f"deaths={last_dth}\n"
        f"resets={last_rst}\n"
    )

    # Insert the new run section above the `[user.<id>.finished]` line
    lines.insert(finished_line_index, new_run_section)

    # Write the updated content back to the file
    with open('data.ini', 'w') as f:
        f.writelines(lines)

    print(f"Summary for user {user_id} added successfully.")

def playGame():
    selectPort()
    summarizeRun(user_data[curr_user]['id'])


createFile()
if input("Have you already played the game (y/n)") == "y":
    login()
    playGame()
else:
    registerUser(input("Enter Name: "), input("Enter Phone: "))
    playGame()
