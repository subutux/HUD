from pgu import gui
import os.path
import icon_font_to_png
whereami = os.path.dirname(os.path.realpath(__file__))


class mdiIcons(object):
    """
    Class for easy converting font icon to a gui.Image
    """

    def __init__(self, css_file, ttf_file):
        """

        @css_file the css file of the webfont

        @ttf_file the font file of the webfont
        """
        self.icons = icon_font_to_png.IconFont(css_file, ttf_file, True)

    def icon(self, iconName, size=16, color="black", scale="auto"):
        """
        get a gui.Image from the icon font

        @iconName the css name of the icon
                          Note: homeAssistant uses a mdi: prefix & is converted
                                        to our prefix
        @size the icon size in px (w=h), default 16
        @color the color of the icon you want, default black
        @scale the scaling to use, default auto
        """
        if iconName.startswith("mdi:"):
            iconName = iconName.replace('mdi:', 'mdi-', 1)

        if not iconName.startswith("mdi-"):
            iconName = "mdi-" + iconName
        file = "{}-x{}-c{}-s{}-HUD.png".format(
            iconName, str(size), color, str(scale))
        # if we find a file in the tmp folder, use that
        if os.path.isfile("{}/{}".format("/tmp", iconName)):
            return gui.Image("{}/{}".format("/tmp", iconName))

        self.icons.export_icon(iconName, size, filename=file,
                               export_dir="/tmp", color=color, scale=scale)
        return gui.Image("{}/{}".format("/tmp", file))


icons = mdiIcons(whereami + "/pgu.theme/mdi/materialdesignicons.css",
                 whereami + "/pgu.theme/mdi/materialdesignicons-webfont.ttf")
