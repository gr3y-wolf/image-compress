from io import BytesIO
from PIL import Image
import whatimage
import pyheif
from helpers import get_size_format
from utils import has_transparency


def compress_img(blob,filename, ext,image_size,new_size_ratio=0.9,quality=65,width=None,height=None):
    # load the image to memory
    fmt = whatimage.identify_image(blob)
    print('>>>>>>>>>>>>>>>    image stream format  ==>>> ', fmt)
    if fmt in ['heic', 'avif']:
        return convert_heic(image=blob, size=image_size, quality=quality)
    else:
        img = Image.open(BytesIO(blob))
        img.load()
        print('[*] Image format is => ',img.format)
        print('[*] Image info => ',img.info)
        print('[*] Image mode  => ', img.mode)
        # print the original image shape
        print("[*] Image resolution :=>", img.size)
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
            to_jpg = False
            if img.format == "JPEG":
                img = img.convert("RGB")
                img.save(out_img, format="jpeg", quality=quality, optimize=True)
            elif img.format == "PNG":
                
                # if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                if has_transparency(img):
                    print('[!!!] Image transparent..., Not changing to jpeg')
                    print("saving PNG file as PNG file")
                    img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
                    img.save(out_img, format="png", quality=quality, optimize=True)
                    
                else:
                    print('converting PNG to JPG format')
                    to_jpg = True
                    img = img.convert("RGB")
                    img.save(out_img, format='jpeg', quality=quality+10, optimize=True)
            else:
                print("[*] Image format is :", img.format)
                # img.save(out_img, format=img.format, quality=quality, optimize=True)
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
            return out_img, to_jpg
        else:
            print("something happened, cant create obj stream")
        # return out_img




# with open('demo.heic', 'rb') as f:
#     data = f.read()


# compress_img(blob=data, image_size=25138412)

def convert_heic(image, size, quality, ext='jpeg'):
    print('begin converting heic')
    output = BytesIO()
    to_jpg = True
    try:
        i = pyheif.read_heif(image)
        # print(i)
        #  # Extract metadata etc
        # #  for metadata in i.metadata or []:
        # #      if metadata['type']=='Exif':
        #          # do whatever
        
         # Convert to other file format jpeg
        pi = Image.frombytes(i.mode, i.size, i.data,"raw", i.mode,  i.stride)
        pi.load()
        # print('[*] Image info => ',pi.info)
        # print('[*] Image mode  => ', pi.mode)
        if pi.mode != 'RGB':
            pi = pi.convert('RGB')
        pi.save(output, format="jpeg", quality=quality-40, optimize=True)

        # get the new image size in bytes
        new_image_size = output.tell()
        # print the new size in a good format
        print("[+] Size after compression:", get_size_format(new_image_size))
        # calculate the saving bytes
        saving_diff = new_image_size - size
        # print the saving percentage
        print(f"[+] Image size change: {saving_diff/size*100:.2f}% of the original image size.")
        output.seek(0)       ## this is very important otherwise image data would be lost.
        return output, to_jpg
    except Exception as e:
        print('error converting heic file to jpg')
        print(str(e))
        raise(e)