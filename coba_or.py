index = 0
while True:
    print("Halo")
    if index == 3 or index == 7:
        send = "Halo " + str(index)
        print(send)
    index += 1 
    if index > 10:
        break