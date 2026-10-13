ENTRY(tick)
SECTIONS {
 . = 0x08680000;
 .text : { KEEP(*(.text.tick)) *(.text*) *(.rodata*) }
 .data : { *(.data*) }
 .bss : { *(.bss*) *(COMMON) }
 ASSERT(SIZEOF(.data) == 0, "No mutable globals")
 ASSERT(SIZEOF(.bss) == 0, "No implicit RAM")
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }
}
