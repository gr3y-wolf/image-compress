from io import BytesIO
from PIL import Image
import whatimage
import pyheif
from helpers import get_size_format


def compress_img(
    blob,
    filename, ext,
    image_size,
    new_size_ratio=0.9,
    quality=90,
    width=None,
    height=None,
    to_jpg=True,
):
    # load the image to memory
    fmt = whatimage.identify_image(blob)
    print('>>>>>>>>>>>>>>>    image stream format  ==>>> ', fmt)
    if fmt in ['heic', 'avif']:
        return convert_heic(image=blob, ext=ext, quality=65)
    else:
        img = Image.open(BytesIO(blob))
        img.load()
        print(img.format)
        # print the original image shape
        print("[*] Image shape:", img.size)
        out_img = BytesIO()
        # get the original image size in bytes
        # image_size = os.path.getsize(image_name)
        # print the size before compression/resizing
        print("[*] Size before compression:", get_size_format(image_size))
        if new_size_ratio < 1.0:
            # if resizing ratio is below 1.0, then multiply width & height with this ratio to reduce image size
            img = img.resize(
                (int(img.size[0] * new_size_ratio), int(img.size[1] * new_size_ratio)),
                Image.ANTIALIAS,
            )
            # print new image shape
            print("[+] New Image shape:", img.size)
        elif width and height:
            # if width and height are set, resize with them instead
            img = img.resize((width, height), Image.ANTIALIAS)
            # print new image shape
            print("[+] New Image shape:", img.size)
        try:
            # save the image with the corresponding quality and optimize set to True
            if img.format == "JPEG":
                img.save(out_img, format="jpeg", quality=quality, optimize=True)
            # elif img.format == "PNG":
            #     print("saving PNG file as png file")
            #     img.save(out_img, format="jpeg", quality=quality, optimize=True)
            else:
                print("[*] Image format is :", img.format)
                img.save(out_img, format=img.format, quality=quality, optimize=True)
        except OSError:
            print("[*] Image format is :", img.format)
            # convert the image to RGB mode first
            img = img.convert("RGB")
            # save the image with the corresponding quality and optimize set to True
            img.save(out_img, format="jpeg", quality=quality, optimize=True)
        except Exception as e:
            print('------------------compression engine failed---------------')
            print(e)
        # print("[+] New file saved:", new_filename)
        # get the new image size in bytes
        new_image_size = out_img.tell()
        # print the new size in a good format
        print("[+] Size after compression:", get_size_format(new_image_size))
        # calculate the saving bytes
        saving_diff = new_image_size - image_size
        # print the saving percentage
        print(
            f"[+] Image size change: {saving_diff/image_size*100:.2f}% of the original image size."
        )
        out_img.seek(0)
        if out_img.getbuffer().nbytes > 1:
            print(" now we can send object stream to s3")
            return out_img
        else:
            print("something happened, cant create obj stream")
        # return out_img




# with open('demo.heic', 'rb') as f:
#     data = f.read()


# compress_img(blob=data, image_size=25138412)

def convert_heic(image, ext, quality):
    print('begin converting heic')
    output = BytesIO()
    try:
        i = pyheif.read_heif(image)
        #  # Extract metadata etc
        # #  for metadata in i.metadata or []:
        # #      if metadata['type']=='Exif':
        #          # do whatever
        
         # Convert to other file format jpeg
        pi = Image.frombytes(i.mode, i.size, i.data,"raw", i.mode,  i.stride)
        pi.load()
        pi.save(output, format="jpeg", quality=60, optimize=True)
        output.seek(0)       ## this is very important otherwise image data would be lost.
        return output
    except Exception as e:
        print('error converting heic file to jpg')
        print(str(e))
        raise(e)