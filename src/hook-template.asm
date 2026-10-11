; Original wrapper provenance. Prepare a private hook-template.gba before assembling.
.gba
.open "build/hook-template.gba", 0x08000000
.org 0x08000500
  ldr r0, =frame_wrapper+1
  bx r0
  .pool
.org 0x08651200
frame_wrapper:
  push r4,lr
  ldr r0, =after_original+1
  push r0
  mov r3, 1
  neg r3,r3
  ldr r0, =0x084F0B14
  ldr r1, =0x08000509
  bx r1
after_original:
  ldr r0, =0x08660001
  bl call_r0
  pop r4
  pop r0
  bx r0
call_r0:
  bx r0
  .pool
.close
