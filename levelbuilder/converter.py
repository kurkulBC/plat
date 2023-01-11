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
        if data == (0, 0, 0):
            savedpixels.append(1)
        if data == (0, 255, 0):
            savedpixels.append(2)
        if data == (255, 0, 0):
            savedpixels.append(3)
        if data == (0, 0, 255):
            savedpixels.append(4)
        if data == (255, 0, 255):
            savedpixels.append(5)
        if data == (255, 128, 255):
            savedpixels.append(6)
        if data == (255, 128, 128):
            savedpixels.append([7, -1])
        if data == (128, 60, 60):
            savedpixels.append([8, -1, 0])
        if data == (128, 0, 0):
            savedpixels.append(9)
        if data == (255, 0, 128):
            savedpixels.append([10, 60])
        if data == (192, 192, 192):
            savedpixels.append(11)
        if data == (100, 100, 100):
            savedpixels.append([13, 0])
    if newline:
        newline = False
        posx = 0
        print(f"{savedpixels},")
        savedpixels.clear()
        if posy < 31:
            posy += 1
        else:
            run = False
