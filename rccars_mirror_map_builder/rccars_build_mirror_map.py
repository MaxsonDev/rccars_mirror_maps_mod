import re
import os
import numpy as np

from rccars_sb_file_parser.sb_utils import read_ushort, read_uint, read_float, write_float, write_char, write_uint, write_ushort
from rccars_sb_file_parser import SBFileParser

MAP_FOLDER_PATH = ""
PROFILE_FOLDER_PATH = ""


class SuperChange:
    def __init__(self, mod_obj, axis):
        self.mod_obj = mod_obj
        self.axis = axis
        self.axis_dict = {
            'X': 0,
            'Z': 1,
            'Y': 2
        }

    def get_axis_num(self):
        return self.axis_dict[self.axis]

    def change_deafult_3DPoint(self, chunk):
        point3D = self.mod_obj.get_data_by_chunk(chunk)
        point3D[self.get_axis_num()] = point3D[self.get_axis_num()] * -1
        self.mod_obj.set_chunk_data(chunk, point3D)

    def calculate_3DPoint_offset(self, point3D_1, point3D_2):
        return abs(point3D_1[self.get_axis_num()]) + abs(point3D_2[self.get_axis_num()])

    def change_chunk_540Bh(self):
        chunk_data = self.mod_obj.get_data_by_chunk("540Bh")
        chunk_data[0][self.get_axis_num()] = chunk_data[0][self.get_axis_num()] * -1


class Change_COLL_Data(SuperChange):
    def change(self):
        # список чанков, в которых надо изменить ось
        chunk_list = ["7099h"]
        for chunk in chunk_list:
            if self.mod_obj.is_chunk_exist(chunk) is False:
                continue
            # "7099h", "709Ah"
            if chunk == "7099h":
                if self.mod_obj.is_chunk_exist("709Ah"):
                    self.change_chunk_7099h_709Ah()
        self.change_collision_data()
    
    def change_chunk_7099h_709Ah(self):
        point_7099h = self.mod_obj.get_data_by_chunk("7099h")
        point_709Ah = self.mod_obj.get_data_by_chunk("709Ah")
        point_7099h_copy = point_7099h.copy()
        point_709Ah_copy = point_709Ah.copy()
        point_7099h[self.get_axis_num()] = point_709Ah_copy[self.get_axis_num()] * -1
        point_709Ah[self.get_axis_num()] = point_7099h_copy[self.get_axis_num()] * -1
        self.mod_obj.set_chunk_data("7099h", point_7099h)
        self.mod_obj.set_chunk_data("709Ah", point_709Ah)
    
    def change_collision_data(self):
        # matrix_data_809Dh = np.array([], dtype=np.ushort)
        # matrix_data_809Ch = np.array([], dtype=np.ushort)
        # matrix_data_1500h = np.array([], dtype=np.ushort)
        # matrix_data_349Fh = np.array([], dtype=np.ushort)
        data_809Dh = np.array(self.mod_obj.data_809Dh, dtype=np.ushort)
        data_809Ch = np.array(self.mod_obj.data_809Ch, dtype=np.ushort) 
        data_1500h = np.array(self.mod_obj.data_1500h, dtype=np.ushort)
        data_349Fh = np.array(self.mod_obj.data_349Fh, dtype=np.ushort)
        pointer_list_of_data_1500h = np.array(self.mod_obj.create_pointer_list_for_face_bit_mask_list())

        count_data_349Fh_and_809Ch = 0
        point_1500h = 0

        # 1. Построим матрицу для всех данных COLL
        print("1. Построим матрицу для всех данных COLL")
        matrix_data_809Dh = []
        matrix_data_809Ch = []
        matrix_data_1500h = []
        matrix_data_349Fh = []
        
        x_vox_length, z_vox_length, y_vox_length = self.mod_obj.get_coll_vox_matrix_resolution()
        x_vox_count = 0
        while x_vox_count < x_vox_length:
            z_vox_count = 0
            z_axis_data_809Dh = []
            z_axis_data_809Ch = []
            z_axis_data_1500h = []
            z_axis_data_349Fh = []
            while z_vox_count < z_vox_length:
                y_vox_count = 0
                y_axis_data_809Dh = []
                y_axis_data_809Ch = []
                y_axis_data_1500h = []
                y_axis_data_349Fh = []
                while y_vox_count < y_vox_length:
                    print(f"X: {x_vox_count} | Z: {z_vox_count} | Y: {y_vox_count}")
                    # рассчитаем линейный указатель на матрицу
                    matrix_point = y_vox_count + y_vox_length * (z_vox_count + z_vox_length * x_vox_count)
                    # получим информацию по количеству мешей в вокселе
                    el_809Dh = data_809Dh[matrix_point]
                    # добави в новый список Y строк
                    y_axis_data_809Dh.append(el_809Dh)
                    # если количесвто мешей в вокселе не равно 0, то добавим другие данные вокселя
                    if el_809Dh != 0:
                        for _ in range(el_809Dh):
                            # возьмем элемент из 809Ch
                            el_809Ch = data_809Ch[count_data_349Fh_and_809Ch]
                            # возьмем элемент из 809Ch
                            el_349Fh = data_349Fh[count_data_349Fh_and_809Ch]
                            # посчитаем сколько байт битовой маски надо собрать в список
                            start_slice = pointer_list_of_data_1500h[point_1500h]
                            try:
                                end_slice = pointer_list_of_data_1500h[point_1500h + 1]
                                face_mask = data_1500h[start_slice:end_slice]
                            except:
                                face_mask = data_1500h[start_slice:]
                            # добавим данные в списки строки Y
                            y_axis_data_809Ch.append(el_809Ch)
                            y_axis_data_349Fh.append(el_349Fh)
                            y_axis_data_1500h.append(face_mask)
                            count_data_349Fh_and_809Ch += 1
                            point_1500h += 1
                    y_vox_count += 1
                # реверсируем список Y осей, если отражение идет по оси Y
                if self.axis == "Y":
                    y_axis_data_809Dh.reverse()
                    y_axis_data_809Ch.reverse()
                    y_axis_data_1500h.reverse()
                    y_axis_data_349Fh.reverse()
                z_axis_data_809Dh.append(y_axis_data_809Dh)
                z_axis_data_809Ch.append(y_axis_data_809Ch)
                z_axis_data_1500h.append(y_axis_data_1500h)
                z_axis_data_349Fh.append(y_axis_data_349Fh)
                z_vox_count += 1
            matrix_data_809Dh.append(z_axis_data_809Dh)
            matrix_data_809Ch.append(z_axis_data_809Ch)
            matrix_data_1500h.append(z_axis_data_1500h)
            matrix_data_349Fh.append(z_axis_data_349Fh)
            x_vox_count += 1
        # 2. В случае beach_1 сделать реверс по оси X
        print("2. В случае beach_1 сделать реверс по оси X")
        if self.axis == "X":
            matrix_data_809Dh.reverse()
            matrix_data_809Ch.reverse()
            matrix_data_1500h.reverse()
            matrix_data_349Fh.reverse()
        # 3. Создадим линейную матрицу из данных после реверса по оси
        print("3. Создадим линейную матрицу из данных после реверса по оси")
        new_data_809Dh = []
        new_data_809Ch = []
        new_data_1500h = []
        new_data_349Fh = []
        for z_axis_data_809Dh in matrix_data_809Dh:
            for y_axis_data_809Dh in z_axis_data_809Dh:
                for d in y_axis_data_809Dh:
                    new_data_809Dh.append(d)
        for z_axis_data_809Ch in matrix_data_809Ch:
            for y_axis_data_809Ch in z_axis_data_809Ch:
                for d in y_axis_data_809Ch:
                    new_data_809Ch.append(d)
        for z_axis_data_349Fh in matrix_data_349Fh:
            for y_axis_data_349Fh in z_axis_data_349Fh:
                for d in y_axis_data_349Fh:
                    new_data_349Fh.append(d)
        for z_axis_data_1500h in matrix_data_1500h:
            for y_axis_data_1500h in z_axis_data_1500h:
                for face_mask in y_axis_data_1500h:
                    for d in face_mask:
                        new_data_1500h.append(d)
        # 4. Добавим массивы в объект
        print("4. Добавим массивы в объект")
        self.mod_obj.set_chunk_data("809Dh", new_data_809Dh)
        self.mod_obj.set_chunk_data("809Ch", new_data_809Ch)
        self.mod_obj.set_chunk_data("1500h", new_data_1500h)
        self.mod_obj.set_chunk_data("349Fh", new_data_349Fh)
        
        
class Change_HHID_Data(SuperChange):
    def change(self):
        # список чанков, в которых надо изменить ось
        chunk_list = ["7091h", "8094h"]
        for chunk in chunk_list:
            if self.mod_obj.is_chunk_exist(chunk) is False:
                continue
            # "7091h", "7092h"
            if chunk == "7091h":
                if self.mod_obj.is_chunk_exist("7092h"):
                    self.change_chunk_7091h_7092h()
            elif chunk == "8094h":
                self.change_chunk_list_8094h()
    
    def change_chunk_7091h_7092h(self):
        point_7091h = self.mod_obj.get_data_by_chunk("7091h")
        point_7092h = self.mod_obj.get_data_by_chunk("7092h")
        point_7091h_copy = point_7091h.copy()
        point_7092h_copy = point_7092h.copy()
        point_7091h[self.get_axis_num()] = point_7092h_copy[self.get_axis_num()] * -1
        point_7092h[self.get_axis_num()] = point_7091h_copy[self.get_axis_num()] * -1
        self.mod_obj.set_chunk_data("7091h", point_7091h)
        self.mod_obj.set_chunk_data("7092h", point_7092h)

    def change_chunk_list_8094h(self):
        print("Zerkalim HHID")
        # 1. Разделим данные на 2 массива: битовую матрицу и матрицу битовых масок
        data_8094h_list = self.mod_obj.get_data_by_chunk('8094h')
        x_vox_length, z_vox_length, y_vox_length = self.mod_obj.get_hhid_vox_matrix_resolution()
        voxel_total_size = x_vox_length * z_vox_length * y_vox_length
        on_off_bit_list = [0 for _ in range(voxel_total_size)]
        mesh_bitmask_list = []
        for data_8094h in data_8094h_list:
            # matrix_point = y_vox_count + y_vox_length * (z_vox_count + z_vox_length * x_vox_count)
            coords = data_8094h['xzy_vox_point']
            data = data_8094h['data']
            matrix_point = coords[2] + y_vox_length * (coords[1] + z_vox_length * coords[0])
            on_off_bit_list[matrix_point] = 1
            [mesh_bitmask_list.append(bitmask) for bitmask in data]
        data_on_off = np.array(on_off_bit_list, dtype=np.bool)
        data_mesh_bitmask = np.array(mesh_bitmask_list, dtype=np.ushort)
        # 2. Преобразуем данные в матрицу
        mesh_bitmask_count = 0
        # посчитаем длину маски в байтах
        mesh_bitmask_size = self.mod_obj.get_data_by_chunk('3093h') // 8 + 1
        x_vox_length, z_vox_length, y_vox_length = self.mod_obj.get_hhid_vox_matrix_resolution()
        x_vox_count = 0
        on_off_matrix = []
        mesh_bitmask_matrix = []
        while x_vox_count < x_vox_length:
            z_vox_count = 0
            z_on_off_data = []
            z_mesh_bitmask_data = []
            while z_vox_count < z_vox_length:
                y_vox_count = 0
                y_on_off_data = []
                y_mesh_bitmask_data = []
                while y_vox_count < y_vox_length:
                    print(f"X: {x_vox_count} | Z: {z_vox_count} | Y: {y_vox_count}")
                    matrix_point = y_vox_count + y_vox_length * (z_vox_count + z_vox_length * x_vox_count)
                    on_off = data_on_off[matrix_point]
                    if on_off == 1:
                        mask_start = mesh_bitmask_count * mesh_bitmask_size
                        mask_end = mask_start + mesh_bitmask_size
                        mask = data_mesh_bitmask[mask_start:mask_end]
                        y_mesh_bitmask_data.append(mask)
                        mesh_bitmask_count += 1
                    else:
                        y_mesh_bitmask_data.append(None)
                    y_on_off_data.append(on_off)
                    y_vox_count += 1
                z_on_off_data.append(y_on_off_data)
                z_mesh_bitmask_data.append(y_mesh_bitmask_data)
                z_vox_count += 1
            on_off_matrix.append(z_on_off_data)
            mesh_bitmask_matrix.append(z_mesh_bitmask_data)
            x_vox_count += 1
        # 3. Отзеркалим по оси X
        on_off_matrix.reverse()
        mesh_bitmask_matrix.reverse()
        # 4. Создаем новый список данных с новыми указателями
        new_data_8094h_list = []
        for x_vox_count in range(x_vox_length):
            for z_vox_count in range(z_vox_length):
                for y_vox_count in range(y_vox_length):
                    on_off = on_off_matrix[x_vox_count][z_vox_count][y_vox_count]
                    if on_off == 1:
                        coords = [x_vox_count, z_vox_count, y_vox_count]
                        data = mesh_bitmask_matrix[x_vox_count][z_vox_count][y_vox_count]
                        new_data_8094h_list.append({
                            'xzy_vox_point': coords,
                            'data': data
                        })
        self.mod_obj.set_chunk_data("8094h", new_data_8094h_list)

    def change_chunk_list_8094h_v1(self):
        # 3093h - mesh_count
        data_length = self.mod_obj.get_data_by_chunk('3093h') // 8 + 1
        data_8094h_list = self.mod_obj.get_data_by_chunk('8094h')
        new_data_8094h_list = []
        for i in range(len(data_8094h_list)):
            data_8094h = data_8094h_list[i]
            data_8094h['data'] = [0xFF for _ in range(data_length)]
            new_data_8094h_list.append(data_8094h)
        self.mod_obj.set_chunk_data("8094h", new_data_8094h_list)
        

class Change_MESH_Data(SuperChange):
    def __init__(self, mod_obj, axis, flag_mesh_need_change_face_index):
        super().__init__(mod_obj, axis)
        self.flag_mesh_need_change_face_index = flag_mesh_need_change_face_index

    def change(self):
        # список чанков, в которых надо изменить ось
        chunk_list = ["7411h", "7414h", "0617h", "8215h", "8216h", "7029h"]
        for chunk in chunk_list:
            if self.mod_obj.is_chunk_exist(chunk) is False:
                continue
            # "7029h", "7030h"
            # if chunk in ["7029h", "7030h"]:
            #    self.change_deafult_3DPoint(chunk)
            if chunk == "7029h":
                if self.mod_obj.is_chunk_exist("7030h"):
                    self.change_chunk_7029h_7030h()
            elif chunk == "7411h":
                self.change_chunk_7411h()
            elif chunk == "7414h":
                self.change_chunk_7414h()
            elif chunk == "8215h":
                self.change_chunk_8215h()
            elif chunk == "8216h":
                self.change_chunk_8216h()
            elif chunk == "0617h":
                self.change_chunk_0617h()
    
    def change_chunk_7029h_7030h(self):
        point_7029h = self.mod_obj.get_data_by_chunk("7029h")
        point_7030h = self.mod_obj.get_data_by_chunk("7030h")
        if sum(point_7029h) == 0 and sum(point_7030h) == 0:
            return
        point_7029h_copy = point_7029h.copy()
        point_7030h_copy = point_7030h.copy()
        point_7029h[self.get_axis_num()] = point_7030h_copy[self.get_axis_num()] * -1
        point_7030h[self.get_axis_num()] = point_7029h_copy[self.get_axis_num()] * -1
        self.mod_obj.set_chunk_data("7029h", point_7029h)
        self.mod_obj.set_chunk_data("7030h", point_7030h)

    def change_chunk_7411h(self):
        vertex_list = self.mod_obj.get_data_by_chunk("7411h")
        for v_num, v_coords in enumerate(vertex_list):
            vertex_list[v_num][self.get_axis_num()] = v_coords[self.get_axis_num()] * -1
        self.mod_obj.set_chunk_data("7411h", vertex_list)

    def change_chunk_7414h(self):
        point3D_list = self.mod_obj.get_data_by_chunk("7414h")
        point3D_7414h_1, point3D_7414h_2 = [l.copy() for l in point3D_list]
        point3D_7414h_1[self.get_axis_num()] = point3D_list[1][self.get_axis_num()] * -1
        point3D_7414h_2[self.get_axis_num()] = point3D_list[0][self.get_axis_num()] * -1
        self.mod_obj.set_chunk_data("7414h", [point3D_7414h_1, point3D_7414h_2])

    def change_chunk_8215h(self):
        axis_indexes = {
            'X': [2, 4, 6, 8],
            'Z': [0, 1],
            'Y': [3, 5, 7, 9]
        }
        chunk_data = self.mod_obj.get_data_by_chunk("8215h")
        for axis in axis_indexes[self.axis]:
            chunk_data[axis] = chunk_data[axis] * -1
        self.mod_obj.set_chunk_data("8215h", chunk_data)

    def change_chunk_8216h(self):
        chunk_data = self.mod_obj.get_data_by_chunk("8216h")
        chunk_data['3DPoint'][self.get_axis_num()] = chunk_data['3DPoint'][self.get_axis_num()] * -1
        self.mod_obj.set_chunk_data("8216h", chunk_data)

    def change_chunk_0617h(self):
        face_data_list = self.mod_obj.get_data_by_chunk("0617h")
        for f_num, face_data in enumerate(face_data_list):
            # меняем индексы у фэйсов, чтобы они отрисовывались при инвертировании вертексов
            # задается флагом
            if self.flag_mesh_need_change_face_index:
                face_data['data_3419h'].reverse()
                # face_indexes_list = face_data_list[f_num]['data_3419h']
                # face_data_list[f_num]['data_3419h'] = [face_indexes_list[2], face_indexes_list[1], face_indexes_list[0]]
                uv_layers = face_data.get('data_063Ah')
                if uv_layers:
                    for uv_map in face_data['data_063Ah']:
                        uv_indexes = uv_map.get('data_343Fh')
                        if uv_indexes:
                            uv_indexes.reverse()
            # меняем координаты 3Д точек фэйсов
            face_data_list[f_num]['data_7027h'][self.get_axis_num()] = face_data['data_7027h'][self.get_axis_num()] * -1
        self.mod_obj.set_chunk_data("0617h", face_data_list)


class Change_MARK_Data(SuperChange):
    def change(self):
        # список чанков, в которых надо изменить ось
        chunk_list = ["540Bh"]
        for chunk in chunk_list:
            if self.mod_obj.is_chunk_exist(chunk) is False:
                continue
            if chunk == "540Bh":
                self.change_chunk_540Bh()


class Change_INST_Data(SuperChange):
    def change(self):
        # список чанков, в которых надо изменить ось
        chunk_list = ["540Bh"]
        for chunk in chunk_list:
            if self.mod_obj.is_chunk_exist(chunk) is False:
                continue
            if chunk == "540Bh":
                self.change_chunk_540Bh()


class Change_EVOL_Data(SuperChange):
    def change(self):
        # список чанков, в которых надо изменить ось
        chunk_list = ["80D4h"]
        for chunk in chunk_list:
            if self.mod_obj.is_chunk_exist(chunk) is False:
                continue
            if chunk == "80D4h":
                self.change_chunk_80D4h()

    def change_chunk_80D4h(self):
        axis_indexes = {
            'X': [2, 4, 6, 8],
            'Z': [0, 1],
            'Y': [3, 5, 7, 9]
        }
        chunk_data = self.mod_obj.get_data_by_chunk("80D4h")
        for axis in axis_indexes[self.axis]:
            chunk_data[axis] = chunk_data[axis] * -1
        self.mod_obj.set_chunk_data("80D4h", chunk_data)


# REWRITE
class SuperRewrite:
    def __init__(self, mod_obj, fb):
        self.mod_obj = mod_obj
        self.fb = fb

    def rewrite_deafult_3DPoint(self, chunk):
        chunk_str = hex(chunk).replace('0x', '').upper() + 'h'
        point3D = self.mod_obj.get_data_by_chunk(chunk_str)
        [write_float(self.fb, axis) for axis in point3D]

    def rewrite_chunk_540Bh(self):
        # пропустим 4 байта
        self.fb.read(4)
        transform_data = self.mod_obj.get_data_by_chunk("540Bh")
        for data_list in transform_data:
            [write_float(self.fb, axis_value) for axis_value in data_list]


class Rewrite_COLL_Data(SuperRewrite):
    def rewrite(self):
        self.fb.seek(self.mod_obj.start_address + 10)
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)
            if chunk in [0x7099, 0x709A]:
                self.rewrite_deafult_3DPoint(chunk)
            elif chunk == 0x809D:
                self.rewrite_chunk_809Dh()
            elif chunk == 0x809C:
                self.rewrite_chunk_809Ch()
            elif chunk == 0x1500:
                self.rewrite_chunk_1500h()
            elif chunk == 0x349F:
                self.rewrite_chunk_349Fh()
            else:
                self.fb.seek(chunk_end)

            if self.mod_obj.end_address == self.fb.tell():
                break
    
    def rewrite_chunk_809Dh(self):
        coll_matrix = self.mod_obj.get_data_by_chunk("809Dh")
        [write_ushort(self.fb, vox) for vox in coll_matrix]
        
    def rewrite_chunk_809Ch(self):
        mesh_point_list = self.mod_obj.get_data_by_chunk("809Ch")
        [write_ushort(self.fb, m_point) for m_point in mesh_point_list]

    def rewrite_chunk_1500h(self):
        # пропустим 4 байта - длинна данных
        self.fb.read(4)
        face_mask_list = self.mod_obj.get_data_by_chunk("1500h")
        [write_char(self.fb, face_byte) for face_byte in face_mask_list]
    
    def rewrite_chunk_349Fh(self):
        # пропустим 4 байта - длинна данных
        self.fb.read(4)
        face_count_list = self.mod_obj.get_data_by_chunk("349Fh")
        [write_uint(self.fb, face_count) for face_count in face_count_list]
    
    
class Rewrite_HHID_Data(SuperRewrite):
    def rewrite(self):
        self.fb.seek(self.mod_obj.start_address + 10)
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)
            if chunk in [0x7091, 0x7092]:
                self.rewrite_deafult_3DPoint(chunk)
            elif chunk == 0x8094:
                # откатим назад на 6 байт(отктаим прочитанные chunk + chunk_end), чтобы начать перезапись с первого чанка
                self.fb.seek(self.fb.tell() - 6)
                self.rewrite_chunk_8094h()
            else:
                self.fb.seek(chunk_end)

            if self.mod_obj.end_address == self.fb.tell():
                break
    
    def rewrite_chunk_8094h(self):
        data_8094h_list = self.mod_obj.get_data_by_chunk('8094h')
        count = 0
        while True:
            # берём чанк
            chunk = read_ushort(self.fb)
            # если чанк == 8094h, то перезаписываем
            if chunk == 0x8094:
                # пропускаем 4 байта адрес
                self.fb.read(4)
                data_8094h = data_8094h_list[count]
                for d in data_8094h["xzy_vox_point"]:
                    write_ushort(self.fb, d)
                for d in data_8094h["data"]:
                    write_char(self.fb, d)
                count += 1
                continue
            # чанки 8094h закончились. откатим указатель назад на 2 байта
            self.fb.seek(self.fb.tell() - 2)
            break


class Rewrite_MESH_Data(SuperRewrite):
    def rewrite(self):
        self.fb.seek(self.mod_obj.start_address + 10)
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)

            if chunk in [0x7029, 0x7030]:
                self.rewrite_deafult_3DPoint(chunk)
            elif chunk == 0x7411:
                self.rewrite_chunk_7411h()
            elif chunk == 0x7414:
                self.rewrite_chunk_7414h()
            elif chunk == 0x8215:
                self.rewrite_chunk_8215h()
            elif chunk == 0x8216:
                self.rewrite_chunk_8216h()
            elif chunk == 0x0617:
                self.rewrite_chunk_0617h(chunk_end)
            else:
                self.fb.seek(chunk_end)

            if self.mod_obj.end_address == self.fb.tell():
                break

    def rewrite_chunk_7411h(self):
        # пропустим 4 байта
        self.fb.read(4)
        vertex_list = self.mod_obj.get_data_by_chunk("7411h")
        for vertex_coords in vertex_list:
            [write_float(self.fb, axis_coord) for axis_coord in vertex_coords]

    def rewrite_chunk_7414h(self):
        # пропустим 4 байта
        self.fb.read(4)
        point3D_list = self.mod_obj.get_data_by_chunk("7414h")
        for point3D in point3D_list:
            [write_float(self.fb, axis_coord) for axis_coord in point3D]

    def rewrite_chunk_8215h(self):
        vertex_coords = self.mod_obj.get_data_by_chunk("8215h")
        [write_float(self.fb, axis_coord) for axis_coord in vertex_coords]

    def rewrite_chunk_8216h(self):
        chunk_data = self.mod_obj.get_data_by_chunk("8216h")
        write_float(self.fb, chunk_data['float'])
        [write_float(self.fb, axis_coord) for axis_coord in chunk_data['3DPoint']]

    def rewrite_chunk_0617h(self, face_data_end):
        # пропустим 4 байта - кол-во блоков данных с face
        self.fb.read(4)
        face_list = self.mod_obj.get_data_by_chunk("0617h")
        # -1, чтобы было 0 - 1 элемент
        face_count = -1
        end_chunk_1882h = None
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)
            if chunk == 0x8218:
                face_count += 1
                end_chunk_1882h = chunk_end
                # пропустим 4 байта - контрольная сумма
                self.fb.read(4)
            elif chunk == 0x3419:
                # пропустим контрольную сумму
                self.fb.read(4)
                face_data = face_list[face_count]
                [write_uint(self.fb, d) for d in face_data['data_3419h']]
            elif chunk == 0x7027:
                face_data = face_list[face_count]
                [write_float(self.fb, d) for d in face_data['data_7027h']]
                # self.fb.seek(end_chunk_1882h)
            elif chunk == 0x063A:
                face_data = face_list[face_count]
                self.rewrite_chunk_063Ah(chunk_end, face_data)
            else:
                self.fb.seek(chunk_end)

            if face_data_end == self.fb.tell():
                break

    def rewrite_chunk_063Ah(self, uv_chunk_end, face_data):
        # пропустим 4 байта - кол-во блоков данных с uv
        self.fb.read(4)
        uv_layer_list = face_data['data_063Ah']
        # -1, чтобы было 0 - 1 элемент
        uv_count = -1
        end_chunk_023Bh = None
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)
            if chunk == 0x023B:
                uv_count += 1
                end_chunk_023Bh = chunk_end
            elif chunk == 0x343F:
                # пропустим контрольную сумму
                self.fb.read(4)
                uv_data = uv_layer_list[uv_count]
                [write_uint(self.fb, d) for d in uv_data['data_343Fh']]
                self.fb.seek(end_chunk_023Bh)
            else:
                self.fb.seek(chunk_end)

            if uv_chunk_end == self.fb.tell():
                break


class Rewrite_MARK_Data(SuperRewrite):
    def rewrite(self):
        self.fb.seek(self.mod_obj.start_address + 10)
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)
            if chunk == 0x540B:
                self.rewrite_chunk_540Bh()
            else:
                self.fb.seek(chunk_end)

            if self.mod_obj.end_address == self.fb.tell():
                break


class Rewrite_INST_Data(SuperRewrite):
    def rewrite(self):
        self.fb.seek(self.mod_obj.start_address + 10)
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)
            if chunk == 0x540B:
                self.rewrite_chunk_540Bh()
            else:
                self.fb.seek(chunk_end)

            if self.mod_obj.end_address == self.fb.tell():
                break


class Rewrite_EVOL_Data(SuperRewrite):
    def rewrite(self):
        self.fb.seek(self.mod_obj.start_address + 10)
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)
            if chunk == 0x80D4:
                self.rewrite_chunk_80D4h()
            else:
                self.fb.seek(chunk_end)

            if self.mod_obj.end_address == self.fb.tell():
                break

    def rewrite_chunk_80D4h(self):
        vertex_coords = self.mod_obj.get_data_by_chunk("80D4h")
        [write_float(self.fb, axis_coord) for axis_coord in vertex_coords]


class RewritePeoplePath:
    def __init__(self, file_path, axis):
            self.axis_dict = {
                'X': 1,
                'Z': 2,
                'Y': 3
            }
            self.file_path = file_path
            self.axis = axis
            self.fb = None
            self.frame_count = None
            self.data = []

    def run(self):
        try:
            self.fb = open(self.file_path, "rb+")
            self._get_data()
            self._change_data()
            self._rewrite_data()
        except Exception as ex:
            raise ex
        finally:
            self.fb.close()

    def _get_data(self):
        self.fb.seek(0, 0)
        # headers
        self.frame_count = read_uint(self.fb)
        [self.fb.read(4) for _ in range(3)]
        # data
        for _ in range(self.frame_count):
            frame_data = [read_float(self.fb) for _ in range(8)]
            self.data.append(frame_data)

    def _change_data(self):
        for frame_data in self.data:
            frame_data[self.axis_dict[self.axis]] = frame_data[self.axis_dict[self.axis]] * -1
            frame_data[4] = frame_data[4] * -1

    def _rewrite_data(self):
        self.fb.seek(0, 0)
        # пропустим headers
        [self.fb.read(4) for _ in range(4)]
        for i in range(self.frame_count):
            frame_data = self.data[i]
            for float_count in range(8):
                if float_count == self.axis_dict[self.axis] or float_count == 4:
                    write_float(self.fb, frame_data[float_count])
                else:
                    self.fb.read(4)


class RCCarsBuildReverseMap:
    def __init__(self, 
                 file_path, 
                 axis,
                 map_name,
                 flag_reverse_map=False,
                 flag_revers_people_paths=False,
                 flag_mesh_need_change_face_index=False):
        if len(file_path) == 0:
            raise RuntimeWarning('Передайте путь к .sb файлу в аргумент file_path.')
        self.file_path = file_path
        if axis.upper() not in ['X', 'Z', 'Y']:
            raise Exception("Ошибочка. Надо указать одну из осей: 'X', 'Z', 'Y'")
        self.axis = axis.upper()
        self.map_name = map_name
        # Params
        self.flag_reverse_map = flag_reverse_map
        # MESH
        self.flag_mesh_need_change_face_index = flag_mesh_need_change_face_index
        # People
        self.flag_revers_people_paths = flag_revers_people_paths
        # ===
        self.parser = None
        self.fb = None

    def run(self):
        if self.flag_reverse_map:
            self.reverse_map()
        if self.flag_revers_people_paths:
            self.reverse_people_paths()

    def reverse_map(self):
        self.parser = SBFileParser(self.file_path)
        self.parser.parse_file()
        DESC = self.parser.get_parsing_result()
        if DESC.mod_type != 'DESC':
            raise Exception("Корневым MOD должен быть DESC.")
        self._open_all_children(DESC, '_change_data')
        self.fb = open(self.file_path, "r+b")
        try:
            self._open_all_children(DESC, '_rewrite_data')
        except Exception as ex:
            raise ex
        finally:
            self.fb.close()

    def reverse_people_paths(self):
        # 1. Получим список файлов
        file_list = os.listdir(PROFILE_FOLDER_PATH)
        # 2. Отфильтруем пути и найдем нужный путь
        people_paths = []
        for f_name in file_list:
            if re.findall(rf"{self.map_name}.+\.dat$", f_name):
                people_paths.append(f"{PROFILE_FOLDER_PATH}\\{f_name}")
        if len(people_paths) == 0:
            return
        # 3. Изменим направления
        for f_path in people_paths:
            rw_people = RewritePeoplePath(f_path, axis=self.axis)
            rw_people.run()


    def _open_all_children(self, mod_obj, fn_name):
        if fn_name not in ['_change_data', '_rewrite_data']:
            raise Exception("Неправильно указано название функции. Ожидаемые имена функций: '_change_data', '_rewrite_data'")
        self.__getattribute__(fn_name)(mod_obj)

        for mod_type in self.parser.mods_str_list:
            child_mod_list = mod_obj.get_child_mod_list(mod_type)
            if child_mod_list is None:
                continue
            for child_mod in child_mod_list:
                self._open_all_children(child_mod, fn_name)

    def _change_data(self, mod_obj):
        if mod_obj.mod_type == 'MESH':
            changer = Change_MESH_Data(mod_obj, self.axis, self.flag_mesh_need_change_face_index)
            changer.change()
        elif mod_obj.mod_type == 'COLL':
            changer = Change_COLL_Data(mod_obj, self.axis)
            changer.change()
        elif mod_obj.mod_type == 'HHID':
            changer = Change_HHID_Data(mod_obj, self.axis)
            changer.change()
        elif mod_obj.mod_type == 'MARK':
            changer = Change_MARK_Data(mod_obj, self.axis)
            changer.change()
        elif mod_obj.mod_type == 'INST':
            changer = Change_INST_Data(mod_obj, self.axis)
            changer.change()
        elif mod_obj.mod_type == 'EVOL':
            changer = Change_EVOL_Data(mod_obj, self.axis)
            changer.change()

    def _rewrite_data(self, mod_obj):
        if mod_obj.mod_type == 'MESH':
            rewriter = Rewrite_MESH_Data(mod_obj, self.fb)
            rewriter.rewrite()
        elif mod_obj.mod_type == 'COLL':
            rewriter = Rewrite_COLL_Data(mod_obj, self.fb)
            rewriter.rewrite()
        elif mod_obj.mod_type == 'HHID':
            rewriter = Rewrite_HHID_Data(mod_obj, self.fb)
            rewriter.rewrite()
        elif mod_obj.mod_type == 'MARK':
            rewriter = Rewrite_MARK_Data(mod_obj, self.fb)
            rewriter.rewrite()
        elif mod_obj.mod_type == 'INST':
            rewriter = Rewrite_INST_Data(mod_obj, self.fb)
            rewriter.rewrite()
        elif mod_obj.mod_type == 'EVOL':
            rewriter = Rewrite_EVOL_Data(mod_obj, self.fb)
            rewriter.rewrite()


if __name__ == '__main__':
    map_list = ["beach_1", "beach_2", "beach_3", "beach_4", "country_1", "country_2", "country_3", "country_4", "urban_1", "urban_2"]
    for map_name in map_list:
        print(f"Zerkalim kartu: {map_name}")
        file_path = f"{MAP_FOLDER_PATH}\\{map_name}.sb"
        revers = RCCarsBuildReverseMap(
            file_path=file_path,
            map_name=map_name,
            axis='X',
            flag_reverse_map=True,
            flag_revers_people_paths=False,
            flag_mesh_need_change_face_index=True
            )
        revers.run()
    print("Finish!")
