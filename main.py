from window import Screen
from assembler.rvi import assemble


assemble('examples/fibonacci.rvi')

screen = Screen("1400", "1100")
