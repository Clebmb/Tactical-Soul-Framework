ENTRY(tick)
SECTIONS {
 . = 0x08680000;
 .text : { KEEP(*(.text.tick)) *(.text*) *(.rodata*) }
 .data : { *(.data*) }
 .bss : { *(.bss*) *(COMMON) }
 ASSERT(SIZEOF(.data) == 0, "Ability runtime cannot use initialized mutable globals")
 ASSERT(SIZEOF(.bss) == 0, "Ability runtime must own/initialize explicit RAM; no BSS")
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }
}
