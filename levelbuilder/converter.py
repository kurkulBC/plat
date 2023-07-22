from PIL import Image


def pixel_rgb(imagepath, x, y):
    img = Image.open(imagepath).convert('RGB')
    r, g, b = img.getpixel((x, y))
    a = (r, g, b)
    return a


image = "input.png"

posx = 0
posy = 0
savedpixels = []
newline = False

run = True
while run:
    data = pixel_rgb(image, posx, posy)
    if posx <= 31:
        if posx < 31:
            posx += 1
        else:
            newline = True

        if data == (255, 255, 255):
            savedpixels.append(0)
        elif data == (0, 0, 0):
            savedpixels.append(1)
        elif data == (0, 255, 0):
            savedpixels.append(2)
        elif data == (255, 0, 0):
            savedpixels.append(3)
        elif data == (0, 0, 255):
            savedpixels.append(4)
        elif data == (255, 0, 255):
            savedpixels.append(5)
        elif data == (255, 128, 255):
            savedpixels.append(6)
        elif data == (255, 128, 128):
            savedpixels.append([7, -1])
        elif data == (128, 60, 60):
            savedpixels.append([8, -1, 0])
        elif data == (128, 0, 0):
            savedpixels.append(9)
        elif data == (255, 0, 128):
            savedpixels.append([10, 60])
        elif data == (192, 192, 192):
            savedpixels.append(11)
        elif data == (100, 100, 100):
            savedpixels.append([13, 0])
        elif data == (32, 32, 32):
            savedpixels.append(14)
        elif data == (196, 128, 0):
            savedpixels.append([15, -1])
        elif data == (128, 128, 0):
            savedpixels.append(16)
        elif data == (128, 128, 128):
            savedpixels.append(17)
        elif data == (64, 128, 196):
            savedpixels.append([18, -1])
        elif data == (200, 196, 0):
            savedpixels.append(20)
        elif data == (196, 196, 196):
            savedpixels.append([20, -1])
        elif data == (197, 197, 197):
            savedpixels.append([21, -1])
        elif data == (198, 198, 198):
            savedpixels.append([22, -1])
        elif data == (199, 199, 199):
            savedpixels.append([23, -1])

        elif data == (0, 255, 255):
            savedpixels.append([4, 0])
        elif data == (64, 64, 64):
            savedpixels.append([1, 0])
        elif data == (196, 0, 0):
            savedpixels.append([3, 0])
    if newline:
        newline = False
        posx = 0
        print(f"{savedpixels},")
        savedpixels.clear()
        if posy < 31:
            posy += 1
        else:
            run = False
