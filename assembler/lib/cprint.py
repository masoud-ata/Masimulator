#
# @author:Don Dennis
# cprint.py
#
# Color Print.


class CPrint:
    BLACK = ''
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    warn32 = True
    no_color = False
    warn = True
    fail = True
    failed = False

    message = ""
    colors = {
        BLACK: "black",
        HEADER: "pink",
        OKBLUE: "blue",
        OKGREEN: "green",
        WARNING: "orange",
        FAIL: "red"
    }
    color = colors[BLACK]

    def consume_message(self):
        self.failed = False
        message = CPrint.message
        color = CPrint.color
        CPrint.message = ""
        CPrint.color = CPrint.colors[self.BLACK]
        return color, message

    def cprint_cus(self, bc, msg):
        s = bc
        e = self.ENDC
        if self.no_color:
            s = ''
            e = ''
        # print(s + msg + e)
        CPrint.message = msg

    def cprint(self, msg):
        print(msg)

    def cprint_msg(self, msg):
        self.cprint_cus(self.OKGREEN, msg)
        CPrint.color = CPrint.colors[self.OKGREEN]

    def cprint_msgg(self, msg):
        self.cprint_cus(self.OKGREEN, msg)
        CPrint.color = CPrint.colors[self.OKGREEN]

    def cprint_msgb(self, msg):
        self.cprint_cus(self.OKBLUE, msg)
        CPrint.color = CPrint.colors[self.OKBLUE]

    def cprint_warn(self, msg):
        if not self.failed and self.warn:
            self.cprint_cus(self.WARNING, msg)
            CPrint.color = CPrint.colors[self.WARNING]

    def cprint_fail(self, msg):
        if self.fail:
            self.failed = True
            self.cprint_cus(self.BOLD + self.FAIL, msg)
            CPrint.color = CPrint.colors[self.FAIL]

    def cprint_warn_32(self, msg):
        if self.warn32:
            self.cprint_warn(msg)
            CPrint.color = CPrint.colors[self.WARNING]


cprint = CPrint()
