ENTRY(tick)
SECTIONS {
 . = 0x08680000;
 .text : { KEEP(*(.text.tick)) *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }
}
