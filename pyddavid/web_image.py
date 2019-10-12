"""
pyddavid.web_image
Ver 1.00
2019/10/13
"""

import requests
import io
import urllib
import os


def test_img_url(url):
    check_value = False
    with requests.head(url) as response:
        if response.status_code == 200:
            check_value = True
    
    return check_value


def save_img_from_url(url, output_path, output_filename):
    check_value = False
    with requests.get(url) as response:
        if response.status_code == 200:
            stream_web_img = io.BytesIO(response.content)
            if not os.path.isdir(output_path):
                os.makedirs(output_path)
            with open(output_path + output_filename, 'wb') as out:
                out.write(stream_web_img.read())
                check_value = True
    return check_value


class UrlComponent():
    def __init__(self, class_, value_list):
        self.class_ = class_
        self.value_list = value_list
        self.reset_pointer()
    

    def reset_pointer(self):
        self.pointer = -1


    def get_next(self):
        if self.pointer >= len(self.value_list) - 1:
            return None
        else:
            self.pointer += 1
            return self.value_list[self.pointer]


    def __str__(self):
        return self.class_ + ", " + str(self.value_list)


    def __len__(self):
        return len(self.value_list)


class UrlToComponentsInterpreter():
    def __init__(self, url_batch = None):
        self.component_funcs = {
            "#": self._interpret_number_range,
            "@": self._interpret_enum
        }
        self.urls = []
        self.add_urls_from_url_batch(url_batch)


    def _interpret_number_range(self, paras):
        class_ = "num"
        value_list = []

        # 1st para: start range
        st = 0
        if len(paras) > 1:
            st = int(paras[1])

        # 2nd para: end range
        en = 10 ** len(paras[0])
        if len(paras) > 2:
            en = int(paras[2])
        
        # 3rd para: step
        step = 1
        if len(paras) > 3:
            st = int(paras[3])
        
        # PeddingLeft
        pedding_left = False
        if paras[0][-1].lower() == "l":
            pedding_left = True
            width = len(paras[0]) - 1

        for value in range(st, en + 1, step):
            if pedding_left:
                value_list.append(str(value).zfill(width))
            else:
                value_list.append(str(value))
        
        return UrlComponent(class_, value_list)


    def _interpret_enum(self, paras):
        class_ = "enum"

        if len(paras) > 1:
            value_list = paras[1:]
        else:
            value_list = []
        
        return UrlComponent(class_, value_list)


    def _interpret_const(self, paras):
        class_ = "const"
        value_list = [paras[0]]

        return UrlComponent(class_, value_list)


    def _urls_from_components(self, components):
        new_url_list = []

        if len(components) > 0:
            for i in range(len(components)):
                components[i].reset_pointer()
            new_url = []

            while True:
                if len(new_url) >= len(components):
                    new_url_list.append("".join(new_url))
                    new_url.pop()
                    if len(new_url) == 0:
                        break
                else:
                    next_str = components[len(new_url)].get_next()
                    if next_str != None:
                        new_url.append(next_str)
                    else:
                        components[len(new_url)].reset_pointer()
                        new_url.pop()
                        if len(new_url) == 0:
                            break

        return new_url_list


    def add_urls_from_url_batch(self, url_batch):
        if url_batch != None:
            url_blocks = url_batch.split(" ")
            
            components = []
            for i in range(len(url_blocks)):
                paras = url_blocks[i].split(",")
                components.append(self.component_funcs.get(paras[0][0], self._interpret_const)(paras))
            
            self.urls.extend(self._urls_from_components(components))
    

    def get_urls(self):
        return self.urls


def path_from_url_and_root(url, root, level = -1):
    url_decoded = urllib.parse.unquote(url)
    double_slash_index = url_decoded.find("//")
    if double_slash_index != -1:
        path = url_decoded[(double_slash_index + 2):]
        #path = path.replace("/", "\\")

        if level != -1:
            slash_index = len(path)
            for dummy_i in range(level + 1):
                slash_index = path.rfind("/", 0, slash_index)
            path = path[(slash_index + 1):]

    if root[-1] != "/":
        root = root + "/"
    
    return root + path


def split_path_to_dir_and_filename(path_):
    filename_index = path_.rfind("/") + 1
    dir_ = path_[:filename_index]
    filename = path_[filename_index:]

    return (dir_, filename)


def main():
    pass
    """
    interpreter = UrlToComponentsInterpreter("http://magikan.games-ent.com/d_magikan/img/card/base400/card_ #l,1,9 _ #,0,3 .png")
    urls = interpreter.urls

    target_dir = "D:/Temp/(Webgame Pic)/"
    output_file_list = [path_from_url_and_root(url, target_dir) for url in urls]
    for i in range(len(output_file_list)):
        output_path, output_filename = split_path_to_dir_and_filename(output_file_list[i])
        save_img_from_url(urls[i], output_path, output_filename)
    """


if __name__ == "__main__":
    main()
