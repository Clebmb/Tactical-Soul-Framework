/* Original host-only after-update callback. Private RAM is shared with
 * the Mario example; do not stack both hooks. Volatile preserves the write. */
__attribute__((section(".text.tick"))) void tick(void) {
    (*(volatile unsigned int*)0x0203D000)++;
}
