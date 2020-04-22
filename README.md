# Masimulator
A simple visual 32-bit RISC-V Simulator developed fully in Python and based on the 5-stage pipeline described in the book "Computer Organization and Design RISC-V Edition: The Hardware Software Interface":
https://www.amazon.com/gp/product/0128122757/ref=dbs_a_def_rwt_bibl_vppi_i2

For now it supports only a handful of instructions, such as ADD, SUB, LW, SW, and BEQ, but this is enough to show the functionality of a pipeline for a lab setting. The pipeline supports forwarding and hazard detection, which can be enabled and disabled to observe the difference.

# Simulator's main window
Below is an image of the simulator's window showing the pipeline with forwarding and hazard detection activated.
The register file, data memory, and program memory are arranged from left to right. 

The register file and data memory are modifiable so functionality can be easily tested. The current instruction (in Fetch stage) is shown in green in the program memory. Changes to the register file and data memory are shown in color in their respective window.

There are 3 buttons on the top left, allwoing to step/backstep through the code and to restart the processor.

It is possible to load new assembly files into the program memory by going through the File menu.


![](images/sample_window.png)
