import tkinter as tk
import traceback
import sys

####################################################################################################
###
###     ToolTip
###
###     This class allows to add a ToolTip to a Tkinter widget.
###
###     Autor:  Stefan Rosewig
###
###     V 1.0       first stable release
###     V 1.0.1     minor fix on display
###     V 1.0.2     version info function added
###     V 1.1.0     improvements exception handling

VERSION     = (1,1,0)
VERSION_s   = "%s.%s.%s" %VERSION

class ToolTip(object):
    """ Class creating a tooltip on a widget 
        Usage: ToolTip(<widget>, <text>, <time>, <font>, <fg>, <bg>)
        <widget>  = TkInter widget to create TooTip on, i.e. tk.Button
        <text>    = The text to be shown as ToolTip
        <time>    = Time in milliseconds until fase out of the ToolTip, 2000ms.
                    If <time> is less than 1000ms, the Tooltip is displayed
                    until the mouse has left the widget.
        <font>    = font to be used, by default ("arial","8","normal")
        <fg>      = foreground color (text), default 'black'
        <bg>      = background color, default 'lightyellow' 
    """
    text = ''
    time = 2000
    def __init__(self, widget, text='', time=2000, font=('arial','8','normal'), fg='black', bg='lightyellow'):                                   
        """ ToolTip initialisation, widget is mandatory """
        widget.focus_displayof()                                                #   Identify tkinter widget
        self.widget = widget                                                    #   The widget the tooltip is for
        if type(text) != str:                                                   #   String expected
            raise TypeError("<text> must be a string")
        self.text = text                                                        #   Tooltip text
        if type(time) != int:                                                   #   Integer expected
            raise TypeError("<time> must be an integer")
        self.time = time                                                        #   Display time for ToolTip
        if type(font) != tuple:                                                 #   tuple (font) expected
            raise TypeError("<font> must be a font tuple")
        self.font = font                                                        #   Font to be used
        self.fg = fg                                                            #   foreground color (textcolor)
        self.bg = bg                                                            #   background color
        self.widget.bind("<Enter>", self.__enter)                               #   If mouse enters widget area
        self.widget.bind("<Leave>", self.__leave)                               #   If mouse leaves widget area
        return

    def version_info():
        """ return version info Major, Minor, Subversion """        
        return VERSION_s

    def config(self, text=None, time=None, font=None, fg=None, bg=None):
        """ configuration of ToolTip """
        if text != None:
            if type(text) != str:                                               #   String expected
                raise TypeError("<text> must be a string")
            self.text = text                                                    #   Tooltip text
        if time != None:
            if type(time) != int:                                               #   Integer expected
                raise TypeError("<time> must be an integer")
            self.time = time                                                    #   Display time for ToolTip
        if font != None:
            if type(font) != tuple:                                             #   tuple (font) expected
                raise TypeError("<font> must be a font tuple")
            self.font = font                                                    #   Font to be used
        if fg != None:
            self.fg = fg                                                        #   foreground color (textcolor)
        if bg != None:
            self.bg = bg                                                        #   background color
        return
    
    def __enter(self, event=None):
        """ MousePointer has entered widget so display the Tooltip """
        self.tw = tk.Toplevel(self.widget)                                      #   Create a toplevel widget
        self.tw.overrideredirect(True)                                          #   No frame for the widget
        scr_w = self.widget.winfo_screenwidth()                                 #   Get screen resolution width
        scr_h = self.widget.winfo_screenheight()                                #   Get screen resolution height
        x = self.tw.winfo_pointerx()                                            #   Pointer X-position
        y = self.tw.winfo_pointery()                                            #   Pointer Y-position
        try:
            tk.Label(self.tw,                                                   #   Label in the widget
                     text = self.text,                                          #   Text to show
                     foreground = self.fg,                                      #   define foregroundcolor
                     background = self.bg,                                      #   define backgroundcolor
                     relief = 'ridge',                                          #   Display Style
                     borderwidth = 1,                                           #   1 Pixel Border
                     font = self.font).pack(ipadx=5)                            #   Define Font
        except tk.TclError:
            traceback.print_exc(limit=2, file=sys.stdout)                       #   print Traceback
            self.tw.destroy()                                                   #   close tooltip
        else:
            self.tw.update()                                                    #   Display ToolTip
            try:
                w_posy = self.widget.winfo_rooty()                              #   Get widget Y Position (Top)
                w_posx = self.widget.winfo_rootx()                              #   Get widget X Position (left)
                w_height = self.widget.winfo_height()                           #   Get widget height
                w_width = self.widget.winfo_width()                             #   Get widget width
                t_height = self.tw.winfo_height()                               #   Get ToolTip heigth
                t_width = self.tw.winfo_width()                                 #   Get ToolTip width
                if t_height + self.widget.winfo_rooty() + 50 > scr_h:           #   Check if ToolTip is out of screen bottom
                    y = w_posy - t_height                                       #   Position it above widget
                else:
                    y = w_posy + w_height                                       #   Position it below widget
                if t_width + self.widget.winfo_rootx() + w_width + 5 > scr_w:   #   Check if ToolTip is out of screen rigth
                    x = w_posx - t_width - 5                                    #   Position it on the left
                else:
                    x = w_posx + w_width + -20                                  #   Position it on the right
                self.tw.wm_geometry("+%d+%d" % (x, y))                          #   Set ToolTip Position
            except :
                pass                                                            #   if bad window path nothing happens
            if self.time > 0:
                self.tw.after(self.time, self.__leave)                          #   Start timer
        return
        
    def __leave(self, event=None):
        """ Mousepointer has left the widget so remove the displayed ToolTip """
        try:
            self.tw.destroy()                                                   #   Destroy ToolTip
        except:
            pass
        return
