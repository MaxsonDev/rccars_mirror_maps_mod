import os
import struct

from rccars_sb_file_parser.sb_utils import read_string, read_uint, read_float, read_ushort, write_float, write_char, write_uint, write_ushort

ROOT_FOLDER_PATH = ""

class RCCarsMirror:
    def __init__(self, file_path):
        if len(file_path) == 0:
            raise RuntimeWarning('Передайте путь к .sb файлу в аргумент file_path.')
            
        self.file_path = file_path
        self.fb = open(self.file_path, "r+b")
        self.file_size = self.fb.seek(0, os.SEEK_END)
        self.fb.seek(0)
        self.address_of_axis = None
        self.frame_count = None
        self.data = []
    
    def work(self):
        try:
            self.find_address_of_axis()
            self.get_path_data()
            self.change_path_data2()
            self.rewrite_path_data2()
        except Exception as ex:
            raise ex
        finally:
            self.fb.close()
            
    def find_address_of_axis(self):
        # пропустим первые 8 байт. они не нужны
        self.fb.read(8)
        while True:
            chunk = read_ushort(self.fb)
            end_address = read_uint(self.fb)
            if chunk == 0x0263:
                self.frame_count = read_uint(self.fb)
                self.fb.seek(end_address)
            if chunk == 0x0264:
                print("Chunk nayden!")
                self.address_of_axis = self.fb.tell()
                return
            else:
                self.fb.seek(end_address)
            
            if self.fb.tell() >= self.file_size:
                break

    def get_path_data(self):
        if self.address_of_axis is None:
            print(f"ВНИМАНИЕ!!! В ФАЙЛЕ {self.file_path} НЕ НАЙДЕН АДРЕС ОСИ!!!")
            return
        for _ in range(self.frame_count):
            frame_data = [read_float(self.fb) for _ in range(34)]
            self.data.append(frame_data)

    def change_path_data(self):
        for frame_data in self.data:
            frame_data[1] = frame_data[1] * -1
            frame_data[4] = frame_data[4] * -1

    def rewrite_path_data(self):
        self.fb.seek(self.address_of_axis)
        for i in range(self.frame_count):
            frame_data = self.data[i]
            for float_count in range(34):
                if float_count == 1 or float_count == 4:
                    write_float(self.fb, frame_data[float_count])
                else:
                    self.fb.read(4)

    def change_path_data2(self):
        rotate = -0.99
        for frame_data in self.data:
            # frame_data[1] = 9.481118202209473
            # frame_data[2] = 1.12902452051639557
            # frame_data[3] = -54.391475677490234
            frame_data[4] = 0
            # frame_data[5] = 0
            frame_data[6] = 0
            # frame_data[5] = 0
            #rotate += 0.01
            #if rotate >= 1:
            #    rotate = -0.99
            # for i in range(4, 34):
            #    frame_data[i] = 0

    def rewrite_path_data2(self):
        self.fb.seek(self.address_of_axis)
        # l = [i for i in range(0, 6)]
        l = [4,5,6]
        for i in range(self.frame_count):
            frame_data = self.data[i]
            for float_count in range(34):
                if float_count in l:
                    write_float(self.fb, frame_data[float_count])
                else:
                    self.fb.read(4)

    def change_axis_value(self):
        if self.address_of_axis is None:
            print(f"ВНИМАНИЕ!!! В ФАЙЛЕ {self.file_path} НЕ НАЙДЕН АДРЕС ОСИ!!!")
            return
        x_axis = self.address_of_axis + 4
        rotate_axis = self.address_of_axis + 16
        for val_address in [x_axis, rotate_axis]:
            # 1. Перейдем на адрес и пропустим первые 4 байта
            self.fb.seek(val_address)
            # 2. Получим значение и изменим его
            axis_value = struct.unpack("f", self.fb.read(4))[0]
            axis_value *= -1
            # 3. Снова перейдем на адрес и перезапишем значение
            self.fb.seek(val_address)
            self.fb.write(struct.pack("f", axis_value))


def main():
    if os.path.exists(ROOT_FOLDER_PATH) is False:
        raise Exception(f"Корневого пути {ROOT_FOLDER_PATH} не существует")
    # 1. Заходим в корневую папку
    os.chdir(ROOT_FOLDER_PATH)
    # 2. Получим список папок в корне папки
    folder_list = os.listdir()
    for folder_name in folder_list:
        # 3. Перейдем в папку с путями машинок
        os.chdir(f"{ROOT_FOLDER_PATH}\\{folder_name}")
        # 4. Получим список файлов с путями машинок в данной папке.
        file_list = os.listdir()
        # 5. Заменим все стартовые позици
        for file_name in file_list:
            file_path = f"{ROOT_FOLDER_PATH}\\{folder_name}\\{file_name}"
            print(f"Смотрим файл {file_name}")
            mirror = RCCarsMirror(file_path)
            mirror.work()


def main2():
    file_path = f"{ROOT_FOLDER_PATH}\\Demo1(Surf)\\buggy2.dat"
    mirror = RCCarsMirror(file_path)
    mirror.work()
        
if __name__ == "__main__":
    print("POSHLA ZARA")
    main()
    print("VSYO KLASSNO! KONEC")
    
