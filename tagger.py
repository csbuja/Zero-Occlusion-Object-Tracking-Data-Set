import __future__
import matplotlib
import matplotlib.image
import matplotlib.pyplot
import matplotlib.widgets
import numpy
import os
import os.path
import PIL
import re
import shutil
import sys

def show():
    fig = matplotlib.pyplot.gcf()
    fig.patch.set_visible(False)
    ax = matplotlib.pyplot.gca()
    ax.axis('off')
    matplotlib.pyplot.show()

class Glyph(object):
    def render(self):
        pass

class ImageGlyph(Glyph):
    def __init__(self, image):
        self.image = image

    def render(self):
        matplotlib.pyplot.imshow(self.image)

class VLineGlyph(Glyph):
    def __init__(self, x, minimum_y, maximum_y):
        self.x = x
        self.minimum_y = minimum_y
        self.maximum_y = maximum_y

    def render(self):
        matplotlib.pyplot.vlines(self.x, self.minimum_y, self.maximum_y)

class HLineGlyph(Glyph):
    def __init__(self, y, minimum_x, maximum_x):
        self.y = y
        self.minimum_x = minimum_x
        self.maximum_x = maximum_x

    def render(self):
        matplotlib.pyplot.hlines(self.y, self.minimum_x, self.maximum_x)

def update_box_glpyh(minimum_x, maximum_x, minimum_y, maximum_y):
    line1 = VLineGlyph(minimum_x, minimum_y, maximum_y)
    line2 = VLineGlyph(maximum_x, minimum_y, maximum_y)
    line3 = HLineGlyph(minimum_y, minimum_x, maximum_x)
    line4 = HLineGlyph(maximum_y, minimum_x, maximum_x)
    return [line1, line2, line3, line4]

class BoxGlyph(Glyph):
    def __init__(self, minimum_x, maximum_x, minimum_y, maximum_y):
        self.glphys = update_box_glpyh(minimum_x, maximum_x, minimum_y, maximum_y)

    def render(self):
        for glyph in self.glphys:
            glyph.render()

class DotGlyph(Glyph):
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size

    def render(self):
        matplotlib.pyplot.plot([self.x], [self.y], "r+", markersize=self.size)

class Renderer(object):
    def __init__(self, glyphs):
        self.glyphs = glyphs

    def render(self):
        matplotlib.pyplot.cla()
        for glyph in self.glyphs:
            glyph.render()

class EventState(object):
    bounding_box = 0
    face_clicking = 1

def baseN(num, numerals="abcdefghijklmnopqrstuvwxyz"):
    b = 26
    return ((num == 0) and numerals[0]) or (baseN(num // b, numerals).lstrip(numerals[0]) + numerals[num % b])

class EventHandler(object):
    def __init__(self, renderer, box_glyph, current_ax, image_path, count, dot_glyph):
        self.count = count
        self.image_path = image_path
        self.box_datas = []
        self.face_datas = []
        self.current_ax = current_ax
        self.number_of_people_entered = 0
        self.state = EventState.bounding_box
        self.face_data = [0, 0]
        self.box_data = [0, 0, 0, 0]
        self.box_glyph = box_glyph
        self.dot_glyph = dot_glyph
        self.renderer = renderer
        self.gender = "none"
        self.renderer.render()
        matplotlib.pyplot.ioff()

        self.key_handler = matplotlib.pyplot.connect("key_press_event", self.toggle_selector_wrapper())
        self.rectangle_selector = matplotlib.widgets.RectangleSelector(self.current_ax, self.line_select_callback_wrapper(), drawtype="box", useblit=True, button=[1, 3], minspanx=5, minspany=5, spancoords="pixels")
        self.cursor = matplotlib.widgets.Cursor(self.current_ax)
        self.clicker = None

    def finish(self):
        print self.image_path
        file_name, extension = os.path.splitext(self.image_path)
        count_letter = baseN(self.count)
        with open(self.image_path) as image_file:
            image = PIL.Image.open(image_file)
            cropped_image = image.crop((int(self.box_data[0]), int(self.box_data[2]), int(self.box_data[1]), int(self.box_data[3])))
            cropped_image.save(file_name + "_" + count_letter + extension)

        with open("{}_{}_gender.txt".format(file_name, count_letter), "w") as gender_file:
            gender_file.write(self.gender)

        with open("{}_{}_bounding_box.txt".format(file_name, count_letter), "w") as bounding_box_file:
            bounding_box_file.write("{},{},{},{}".format(int(self.box_data[0]), int(self.box_data[1]), int(self.box_data[2]), int(self.box_data[3])))

        with open("{}_{}_face_point.txt".format(file_name, count_letter), "w") as face_point_file:
            face_point_file.write("{},{}".format(int(self.face_data[0]), int(self.face_data[1])))

    def next_person(self):
        print("next person")
        matplotlib.pyplot.disconnect(self.key_handler)
        self.rectangle_selector.set_active(False)
        matplotlib.pyplot.close("all")
        self.finish()
        print("done")
        return

    def line_select_callback_wrapper(self):
        def line_select_callback(eclick, erelease):
            "eclick and erelease are the press and release events"
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata
            self.box_glyph.glphys = update_box_glpyh(x1, x2, y1, y2)
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])
            self.box_data = [x1, x2, y1, y2]
            self.renderer.render()
            print("({:3.2f}, {:3.2f}) --> ({:3.2f}, {:3.2f})".format(x1, y1, x2, y2))
            print(" The button you used were: {} {}".format(eclick.button, erelease.button))
            self.cursor = matplotlib.widgets.Cursor(self.current_ax)
            self.rectangle_selector.set_active(False)
            self.rectangle_selector = matplotlib.widgets.RectangleSelector(self.current_ax, self.line_select_callback_wrapper(), drawtype="box", useblit=True, button=[1, 3], minspanx=5, minspany=5, spancoords="pixels")
        return line_select_callback

    def click_handler_wrapper(self):
        def click_handler(event):
            if event.button == 1:
                self.face_data = [event.xdata, event.ydata]
                self.dot_glyph.x = event.xdata
                self.dot_glyph.y = event.ydata
                self.dot_glyph.size = 2
                self.renderer.render()
                print("Face is at ({:3.2f}, {:3.2f})".format(self.face_data[0], self.face_data[1]))
        return click_handler

    def toggle_selector_wrapper(self):
        def toggle_selector(event):
            print(self.rectangle_selector.active)
            print(" Key pressed.")
            if self.state == EventState.bounding_box:
                if event.key in ["E", "e"]:
                    print(" Selecting bounding box")
                    print(" ({:3.2f}, {:3.2f}) --> ({:3.2f}, {:3.2f})".format(self.box_data[0], self.box_data[1], self.box_data[2], self.box_data[3]))
                    self.rectangle_selector.set_active(False)
                    self.state = EventState.face_clicking
                    self.clicker = matplotlib.pyplot.connect("button_press_event", self.click_handler_wrapper())
            elif self.state == EventState.face_clicking:
                if event.key in ["E", "e"]:
                    if self.face_data[0] == 0 or self.face_data[1] == 0:
                        print("Invalid face")
                        return
                    print(" Selecting face")
                    print(" ({:3.2f}, {:3.2f})".format(self.face_data[0], self.face_data[1]))
                    matplotlib.pyplot.disconnect(self.clicker)
                    self.next_person()

        return toggle_selector

class FolderHandler(object):
    def __init__(self):
        self.more = True
        self.genders = []
        self.event_handler_lists = []

    def activate(self):
        self.key_handler = matplotlib.pyplot.connect("key_press_event", self.key_handler_wrapper())

    def next(self):
        matplotlib.pyplot.disconnect(self.key_handler)
        matplotlib.pyplot.ion()
        window = matplotlib.pyplot.get_current_fig_manager().full_screen_toggle()
        show()
        matplotlib.pyplot.close("all")

    def end(self):
        self.more = False
        matplotlib.pyplot.disconnect(self.key_handler)
        matplotlib.pyplot.ion()
        window = matplotlib.pyplot.get_current_fig_manager().full_screen_toggle()
        show()
        matplotlib.pyplot.close("all")

    def key_handler_wrapper(self):
        def key_handler(event):
            print("key")
            if event.key in ["M", "m"]:
                print("male")
                self.genders.append("m")
                self.next()
            elif event.key in ["F", "f"]:
                print("female")
                self.genders.append("f")
                self.next()
            elif event.key in ["E", "e"]:
                print("end")
                self.end()
            else:
                print("This is not a valid action, enter male or female (m/f) or e to end")
        return key_handler

def main():
    matplotlib.pyplot.close("all")
    matplotlib.rcParams["keymap.fullscreen"] = "0"
    fig, current_ax = matplotlib.pyplot.subplots()
    N = 100000
    x = numpy.linspace(0.0, 10.0, N)
    folders = sys.argv[1:]
    for folder in sorted(folders):
        folder_handler = FolderHandler()
        i = 0
        while True:
            folder_handler.activate()
            picture_file_names = os.listdir(folder)
            numbers_only = re.compile(r"^\d+\..*$")
            picture_file_names = [x for x in picture_file_names if numbers_only.match(x)]
            first_picture_file_name = picture_file_names[0]
            first_image = matplotlib.image.imread(os.path.join(folder, first_picture_file_name))
            first_image_glyph = ImageGlyph(first_image)
            renderer = Renderer([first_image_glyph])
            print("Enter the gender of the person m/f (e to quit)")
            matplotlib.pyplot.ioff()
            renderer.render()
            window = matplotlib.pyplot.get_current_fig_manager().full_screen_toggle()
            show()
            if not folder_handler.more:
                break
            event_handlers = []
            for picture_file_name in sorted(picture_file_names):
                fig, current_ax = matplotlib.pyplot.subplots()
                N = 100000
                x = numpy.linspace(0.0, 10.0, N)

                image = matplotlib.image.imread(os.path.join(folder, picture_file_name))
                image_glyph = ImageGlyph(image)
                box_glyph = BoxGlyph(0, 0, 0, 0)
                height, width, _ = image.shape
                dot_glyph = DotGlyph(width/2, height/2, 0)
                renderer = Renderer([image_glyph, box_glyph, dot_glyph])
                event_handler = EventHandler(renderer, box_glyph, current_ax, os.path.join(folder, picture_file_name), i, dot_glyph)
                event_handler.gender = folder_handler.genders[-1]
                event_handlers.append(event_handler)
                matplotlib.pyplot.ioff()
                window = matplotlib.pyplot.get_current_fig_manager().full_screen_toggle()
                show()
            folder_handler.event_handler_lists.append(event_handlers)
            file_name, extension = os.path.splitext(os.path.join(folder, first_picture_file_name))
            count_letter = baseN(i)
            print("all")
            with open(os.path.join(folder, "{}_bounding_boxes.txt".format(count_letter)), "w") as bounding_boxes_file:
                for event_handler in event_handlers:
                    box_data = event_handler.box_data
                    bounding_boxes_file.write("{},{},{},{}\n".format(int(box_data[0]), int(box_data[2]), int(box_data[1] - box_data[0]), int(box_data[3] - box_data[2])))

            with open(os.path.join(folder, "{}_gender.txt".format(count_letter)), "w") as gender_file:
                gender_file.write(folder_handler.genders[-1])
            i = i + 1

        with open(os.path.join(folder, "genders.txt"), "w") as genders_file:
            for gender in folder_handler.genders:
                genders_file.write("{}\n".format(gender))

        person_count = len(folder_handler.event_handler_lists)
        for picture_file_name, event_handlers in zip(picture_file_names, zip(*folder_handler.event_handler_lists)):
            file_name, extension = os.path.splitext(os.path.join(folder, picture_file_name))
            image = matplotlib.image.imread(os.path.join(folder, picture_file_name))
            height, width, _ = image.shape
            with open("{}_inria.txt".format(file_name), "w") as annot:
                annot.write("# PASCAL Annotation Version 1.00\n")
                annot.write("\n")
                annot.write("Image filename : \"Train/pos/{}\"\n".format(picture_file_name))
                annot.write("Image size (X x Y x C) : {} x {} x 3\n".format(width, height))
                annot.write("Database : \"The INRIA Rhone-Alpes Annotated Person Database\"\n")
                annot.write("Objects with ground truth : {} {{ {} }}\n".format(len(event_handlers), " ".join(["\"PASperson\""]*len(event_handlers))))
                annot.write("\n")
                annot.write("# Top left pixel co-ordinates : (0, 0)\n")
                for i, event_handler in enumerate(event_handlers):
                    i = i + 1
                    annot.write("\n")
                    annot.write("# Details for object {} (\"PASperson\")\n".format(i))
                    annot.write("# Center point -- not available in other PASCAL databases -- refers\n")
                    annot.write("# to person head center\n")
                    annot.write("Original label for object {} \"PASperson\": \"UprightPerson\"\n".format(i))
                    annot.write("Center point on object {} \"PASperson\" (X, Y) : ({}, {})\n".format(i, int(event_handler.face_data[0]), int(event_handler.face_data[1])))
                    annot.write("Bounding box for object {} \"PASperson\" (Xmin, Ymin) - (Xmax, Ymax) : ({}, {}) - ({}, {})\n".format(i, int(event_handler.box_data[0]), int(event_handler.box_data[2]), int(event_handler.box_data[1]), int(event_handler.box_data[3])))


        try:
            os.mkdir("targeter")
        except OSError:
            pass

        try:
            os.mkdir(os.path.join("targeter", folder))
        except OSError:
            pass

        person_count = len(folder_handler.event_handler_lists)
        for picture_file_name, event_handlers in zip(picture_file_names, zip(*folder_handler.event_handler_lists)):
            numbers, _ = os.path.splitext(picture_file_name)
            file_name, extension = os.path.splitext(os.path.join(folder, picture_file_name))
            image = matplotlib.image.imread(os.path.join(folder, picture_file_name))
            height, width, _ = image.shape
            with open(os.path.join("targeter", folder, "{}.txt".format(numbers)), "w") as annot:
                for event_handler in event_handlers:
                    annot.write("{},{},{},{}\n".format(int(event_handler.box_data[0]), int(event_handler.box_data[3]), int(event_handler.box_data[1] - event_handler.box_data[0]), int(event_handler.box_data[3] - event_handler.box_data[2])))
            try:
                os.remove(os.path.join("targeter", folder, "{}".format(picture_file_name)))
            except OSError:
                pass

            try:
                shutil.copyfile(os.path.join(folder, "{}".format(picture_file_name)), os.path.join("targeter", folder, "{}".format(picture_file_name)))
            except OSError:
                pass

        bound_boxes_only = re.compile(r"^.*_bounding_boxes\.txt$")
        image_files_only = re.compile(r"^\d+\..*$")
        letters_match = re.compile(r"(.*)_bounding_boxes\.txt")
        bounding_boxes_file_names = os.listdir(folder)
        image_file_names = os.listdir(folder)
        bounding_boxes_file_names = [x for x in bounding_boxes_file_names if bound_boxes_only.match(x)]
        image_file_names = [x for x in image_file_names if image_files_only.match(x)]
        try:
            os.mkdir("tracking")
        except OSError:
            pass
        for bounding_box_file_name in bounding_boxes_file_names:
            letters = letters_match.match(bounding_box_file_name).groups()[0]
            try:
                os.mkdir(os.path.join("tracking", folder + letters))
            except OSError:
                pass
            try:
                os.mkdir(os.path.join("tracking", folder + letters, "img"))
            except OSError:
                pass
            for image_file_name in image_file_names:
                try:
                    os.remove(os.path.join("tracking", folder + letters, "img", image_file_name))
                except OSError:
                    pass
                shutil.copyfile(os.path.join(folder, image_file_name), os.path.join("tracking", folder + letters, "img", image_file_name))
                try:
                    os.remove(os.path.join("tracking", folder + letters, "groundtruth_rect.txt"))
                except OSError:
                    pass
                shutil.copyfile(os.path.join(folder, bounding_box_file_name), os.path.join("tracking", folder + letters, "groundtruth_rect.txt"))

        try:
            os.mkdir("INRIA")
        except OSError:
            pass
        try:
            os.mkdir(os.path.join("INRIA", "data"))
        except OSError:
            pass
        try:
            os.mkdir(os.path.join("INRIA", "data", "Annotations"))
        except OSError:
            pass
        try:
            os.mkdir(os.path.join("INRIA", "data", "Images"))
        except OSError:
            pass
        picture_only_match = re.compile(r"^\d+\..*$")
        number_match = re.compile(r"^(\d+)\..*$")
        picture_file_names = os.listdir(folder)
        picture_file_names = [x for x in picture_file_names if picture_only_match.match(x)]

        for picture_file_name in picture_file_names:
            numbers = number_match.match(picture_file_name).groups()[0]
            inria_file_name = "{}_inria.txt".format(numbers)

            try:
                os.remove("INRIA", "data", "Annotations", "{}{}.txt".format(folder, numbers))
            except:
                pass
            try:
                shutil.copyfile(os.path.join(folder, inria_file_name), os.path.join("INRIA", "data", "Annotations", "{}{}.txt".format(folder, numbers)))
            except:
                pass

            _, extension = os.path.splitext(picture_file_name)
            try:
                os.remove("INRIA", "data", "Images", "{}{}{}".format(folder, numbers, extension))
            except:
                pass
            try:
                shutil.copyfile(os.path.join(folder, picture_file_name), os.path.join("INRIA", "data", "Images", "{}{}{}".format(folder, numbers, extension)))
            except:
                pass

        # image = matplotlib.image.imread("./Walking-Image.jpg")
        # image_plot = matplotlib.pyplot.imshow(image)
        # matplotlib.pyplot.show()

if __name__ == "__main__":
    main()

