import os
import struct

from rccars_sb_file_parser.sb_utils import read_string, read_uint, read_float, write_float, write_char, write_uint, write_ushort

PROFILE_FOLDER_PATH = ""


class RewriteRoadcarPath:
    def __init__(self, file_path):
        self.file_path = file_path
        self.fb = None
        self.frame_count = None
        self.data = []

    def run(self):
        try:
            self.fb = open(self.file_path, "rb+")
            self.change_car_data()
            # self.change_wheel_data()
        except Exception as ex:
            raise ex
        finally:
            self.fb.close()

    def change_car_data(self):
        self._get_car_data()
        self._change_car_data()
        self._rewrite_car_data()
        self.data = []

    def _get_car_data(self):
        # headers
        self.fb.seek(0, 0)
        self.fb.read(2)
        str_name = read_string(self.fb)
        if str_name != 'ROADCAR':
            raise "Error net ROADCAR word"
        self.fb.seek(0, 0)
        self.fb.read(0x18)
        self.frame_count = read_uint(self.fb)
        self.fb.read(8)
        # data
        for _ in range(self.frame_count):
            frame_data = [read_float(self.fb) for _ in range(8)]
            self.data.append(frame_data)

    def _change_car_data(self):
        for frame_data in self.data:
            frame_data[1] = frame_data[1] * -1
            frame_data[4] = frame_data[4] * -1
            frame_data[7] = frame_data[7] * -1

    def _rewrite_car_data(self):
        self.fb.seek(0, 0)
        self.fb.read(0x24)
        for i in range(self.frame_count):
            frame_data = self.data[i]
            for float_count in range(8):
                if float_count == 1 or float_count == 4 or float_count == 7:
                    write_float(self.fb, frame_data[float_count])
                else:
                    self.fb.read(4)

    def change_wheel_data(self):
        self._get_wheel_data()
        self._change_wheel_data()
        self._rewrite_wheel_data()

    def _get_wheel_data(self):
        self.fb.seek(0, 0)
        self.fb.read(0x24)
        self.fb.read(self.frame_count * 8 * 4)
        for _ in range(self.frame_count):
            self.data.append([read_uint(self.fb), read_float(self.fb)])

    def _change_wheel_data(self):
        for frame_data in self.data:
            frame_data[1] = frame_data[1] * -1

    def _rewrite_wheel_data(self):
        self.fb.seek(0, 0)
        self.fb.read(0x18)
        self.fb.seek(self.frame_count * 8 * 4)
        for i in range(self.frame_count):
            frame_data = self.data[i]
            for float_count in range(2):
                if float_count == 1:
                    write_float(self.fb, frame_data[float_count])
                else:
                    self.fb.read(4)


def main():
    # 1. Получим список файлов
    file_list = os.listdir(PROFILE_FOLDER_PATH)
    # 2. Отфильтруем пути и найдем нужный путь
    roadcar_paths = []
    for f_name in file_list:
        if f_name.find("rdc") != -1:
            roadcar_paths.append(f"{PROFILE_FOLDER_PATH}\\{f_name}")
    if len(roadcar_paths) == 0:
        return
    # 3. Изменим направления
    for f_path in roadcar_paths:
        rw_people = RewriteRoadcarPath(f_path)
        rw_people.run()


if __name__ == "__main__":
    print("POSHLA ZARA")
    main()
    print("VSYO KLASSNO! KONEC")
