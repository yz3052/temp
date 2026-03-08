import os
import binascii
import time
import matplotlib as m
import qrcode
import cv2
import numpy as np
import random
import string
import itertools
from tqdm import tqdm


##############################################################################
#!- 7z target
##############################################################################



# show file

os.listdir('/data/user/tozhang/backup/raw_data/')

# 71 command


'''
7z a /data/user/tozhang/encrypted/raw_data/equities.centaur-master@a6b2009e541.7z /data/user/tozhang/encrypted/raw_data/equities.centaur-master@a6b2009e541.zip
7z a /data/user/tozhang/encrypted/raw_data/TZ_onenote_20251007.onepkg.7z /users/is/tozhang/Downloads/TZ_onenote_20251007.onepkg; 
'''



##############################################################################
#!- file -> hex
##############################################################################


# P = '/data/user/tozhang/encrypted/raw_data/man.codex-master@23a14be06ae.zip'
# P = '/users/is/tozhang/Download/TZ_onenote_20251007.onepkg'
# P = '/data/user/tozhang/encrypted/raw_data/TZ_onenote_20251007.onepkg'
# P = '/data/user/tozhang/encrypted/raw_data/man.core-master@b4a76189c17.zip'
# P = '/data/user/tozhang/encrypted/raw_data/ahl.marketdata-master@4fa4fc8c764.zip'
# P = '/data/user/tozhang/backup/raw_data/statarb_all_signal.asof20251028.7z'
# P = '/data/user/tozhang/backup/raw_data/equities.alphacapture-admin-master@a1ecb608729.zip'
# P = '/data/user/tozhang/backup/raw_data/yz_codebank.asof20251031.7z'
# P = '/data/user/tozhang/backup/raw_data/swan_all_signal.asof20251028.7z'
P = '/data/user/tozhang/backup/raw_data/data.TRQA.dictionary.7z'



HEX = binascii.b2a_base64(open(P, 'rb').read()).decode('ascii')
    # len = 95_835_633

HEX_CHECKSUM = sum(ord(c) for c in HEX) % 256





##############################################################################
#!- hex -> show
##############################################################################



CHUNK = 2800

print('whole file checksum = ' + str(HEX_CHECKSUM))
print('est. play minutes = ' + str(len(HEX)//CHUNK//2//60))
print('max cnt index = ' + str((len(HEX)-1)//CHUNK))

# add_on = [0, 781] + list(range(3847,4018)) + [4370] \
#          + list(range(4404, 4408)) + [5241, 6040, 7246]
# add_on = [i*CHUNK for i in add_on]


# continue: range(15180 * CHUNK, len(HEX), CHUNK)
for i in range(0 * CHUNK, len(HEX), CHUNK):
# for i in add_on:

    if i%(CHUNK*100) == 0:
        print(round(i / len(HEX), 2), end = ' | ')

    hex = HEX[i: i + CHUNK]
    cnt_str = str(i//CHUNK).zfill(6)
    sum_ord = sum(ord(c) for c in hex)
    hex_checksum_str_1 = str(sum_ord % 16).zfill(3)
    hex_checksum_str_2 = str(sum_ord % 256).zfill(3)
    qr = qrcode.QRCode(
        version=40, box_size=3, border=20,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
    )
    qr.add_data(cnt_str + hex_checksum_str_1 + hex + hex_checksum_str_2)
    qr.make(fit=False)
    img = qr.make_image(fill_color="black", back_color="white")
    cv2.imshow('image', np.array(img.convert('RGB')))

    if i == 0:
        cv2.waitKey(20_000)
    if cv2.waitKey(500) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break
cv2.destroyAllWindows()






##############################################################################
#!- hex -> color show
##############################################################################



P = '/data/user/tozhang/backup/raw_data/ml.research.7z'


IMG_EDGE = 140
PX_SIZE = 7
FRAME_WIDTH = 2


HEX = binascii.hexlify(open(P, 'rb').read())
HEX_lst = np.array(list(HEX))
HEX_lst = np.where(HEX_lst<60,HEX_lst-48,HEX_lst)
HEX_lst = np.where(HEX_lst>60,HEX_lst-87,HEX_lst)
HEX_lst = HEX_lst * 16
HEX_lst = list(HEX_lst)

CHUNK_SIZE = 3 * (IMG_EDGE ** 2) - 79
LEN_HEX = len(HEX)
CHUNK_NUM = (LEN_HEX-1)//(CHUNK_SIZE) + 1



print('total chunk num:' + str(CHUNK_NUM))
print('est. play minutes = ' + str(CHUNK_NUM * 2//60))
def gen_img(data, LEN_DATA, chunk):

    # pixel 2 - keepdata
    # reminder: IMG_EDGE must be <= 256
    # x*150*3 + y*3 +z = len(data) = total number of uint8 values we'd like to keep
    # where x = x1 * 16 + x2;
    KEEPDATA_x1 = LEN_DATA // (IMG_EDGE * 3) // 16
    KEEPDATA_x2 = (LEN_DATA // (IMG_EDGE * 3)) % 16
    KEEPDATA_y1 = LEN_DATA % (IMG_EDGE * 3) // 3 // 16
    KEEPDATA_y2 = (LEN_DATA % (IMG_EDGE * 3) // 3) % 16
    KEEPDATA_z1 = (LEN_DATA % 3) // 16
    KEEPDATA_z2 = (LEN_DATA % 3) % 16

    # pixel 3 - image index
    # chunk = (x * 256 + y) * 256 + z
    # where x = x1*16 + x2
    IDX_z1 = (chunk % 256) // 16
    IDX_z2 = (chunk % 256) % 16
    IDX_z = IDX_z1 * 16 + IDX_z2
    IDX_y1 = int((((chunk - IDX_z) / 256) % 256) // 16)
    IDX_y2 = int((((chunk - IDX_z) / 256) % 256) % 16)
    IDX_y = IDX_y1 * 16 + IDX_y2
    IDX_x1 = int((((chunk - IDX_z) / 256 - IDX_y) / 256) // 16)
    IDX_x2 = int((((chunk - IDX_z) / 256 - IDX_y) / 256) % 16)

    # pixel 1 - checksum
    S = sum(data) + (
        + KEEPDATA_x1 * 16 + KEEPDATA_x2 * 16
        + KEEPDATA_y1 * 16 + KEEPDATA_y2 * 16
        + KEEPDATA_z1 * 16 + KEEPDATA_z2 * 16
        + IDX_x1 * 16 + IDX_x2 * 16 + IDX_y1 * 16
        + IDX_y2 * 16 + IDX_z1 * 16 + IDX_z2 * 16
    )
    BYTE_CHECKSUM_A = S % 100 % 15  # (sum(data) % 16) # S%100%16
    BYTE_CHECKSUM_B = int(str(int(S))[:2]) % 16  # (sum(data) % 11) # int(str(int(S))[:2])%16
    BYTE_CHECKSUM_C = sum(int(s) for s in str(int(S))) % 16  # (sum(data) % 7) # sum(int(s) for s in str(int(S)))%16



    #---------------------------------------------------------------------------------------------------------
    # pixel 4 - hash
    import hashlib
    hash = hashlib.sha256(
        np.array(
            data + [
                KEEPDATA_x1 * 16, KEEPDATA_x2 * 16, KEEPDATA_y1 * 16, KEEPDATA_y2 * 16, KEEPDATA_z1 * 16,
                KEEPDATA_z2 * 16,
                IDX_x1 * 16, IDX_x2 * 16, IDX_y1 * 16, IDX_y2 * 16, IDX_z1 * 16, IDX_z2 * 16,
            ]
        ).tobytes()
    ).hexdigest()
    hash_lst = np.array([ord(h) for h in hash])
    hash_lst = np.where(hash_lst < 60, hash_lst - 48, hash_lst)
    hash_lst = np.where(hash_lst > 60, hash_lst - 87, hash_lst)
    hash_lst = hash_lst * 16
    hash_lst = list(hash_lst)
    #---------------------------------------------------------------------------------------------------------



    # pad data
    if chunk == CHUNK_NUM - 1:
        data.extend([126] * (CHUNK_SIZE - LEN_HEX % CHUNK_SIZE))

    # convert data to images
    img = (
            [BYTE_CHECKSUM_A * 16, BYTE_CHECKSUM_B * 16, BYTE_CHECKSUM_C * 16]
            + [
                KEEPDATA_x1 * 16, KEEPDATA_x2 * 16,
                KEEPDATA_y1 * 16, KEEPDATA_y2 * 16,
                KEEPDATA_z1 * 16, KEEPDATA_z2 * 16
            ]
            + [
                IDX_x1 * 16, IDX_x2 * 16, IDX_y1 * 16,
                IDX_y2 * 16, IDX_z1 * 16, IDX_z2 * 16
            ]
            + hash_lst
            + data
    )

    # image frame
    # img = IMG_EDGE * IMG_EDGE * 3
    img_2 = (
            [0] * 3 * (IMG_EDGE + FRAME_WIDTH * 2) * FRAME_WIDTH
            + list(itertools.chain.from_iterable(
        [
            [0] * 3 * FRAME_WIDTH
            + img[i:i + 3 * IMG_EDGE]
            + [0] * 3 * FRAME_WIDTH
            for i in range(0, len(img), 3 * IMG_EDGE)
        ]
    ))
            + [0] * 3 * (IMG_EDGE + FRAME_WIDTH * 2) * FRAME_WIDTH
    )

    # enlarge image
    img_2 = list(itertools.chain.from_iterable(
        [
            img_2[i:i + 3] * PX_SIZE
            for i in range(0, len(img_2), 3)
        ]
    ))
    img_2 = list(itertools.chain.from_iterable(
        [
            img_2[i:i + 3 * PX_SIZE * (IMG_EDGE + 2 * FRAME_WIDTH)] * PX_SIZE
            for i in range(0, len(img_2), 3 * PX_SIZE * (IMG_EDGE + 2 * FRAME_WIDTH))
        ]
    ))

    img_arr = np.array(img_2).astype(np.uint8)
    img_arr = img_arr.reshape(((IMG_EDGE + 2 * FRAME_WIDTH) * PX_SIZE, (IMG_EDGE + 2 * FRAME_WIDTH) * PX_SIZE, 3))
    return img_arr







#for chunk in tqdm(range(CHUNK_NUM)):
for chunk in [0, 190, 324]:

    # start / end
    idx_s = chunk * CHUNK_SIZE
    idx_e = (chunk + 1) * CHUNK_SIZE

    # read data
    data = HEX_lst[idx_s:idx_e]
    LEN_DATA = len(data)


    img_arr = gen_img(data, LEN_DATA, chunk)
    cv2.imshow('image', img_arr)

    if chunk == 0:
        cv2.waitKey(20_000)

    if cv2.waitKey(1_100) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break
    # cv2.imshow('image', np.zeros(img_arr.shape)+126)
    if cv2.waitKey(100) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break


    # if cv2.waitKey(200) & 0xFF == ord('q'):
    #     cv2.destroyAllWindows()
    #     break

time.sleep(5)
cv2.destroyAllWindows()



