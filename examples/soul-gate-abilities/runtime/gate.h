/* Fixed room14 gate extension; uses the SDK scalar/read definitions. */
static void ownership_barrier(void){
 if(R8(0x02000010)!=4 || R8(0x02000064)!=1 || R8(0x02013266)!=0)return;
 if(R16(0x0201327A)==0 || (R32(0x0200042C)&1u))return;
 if(R32(0x02000088)!=0x0850F7ECu)return; /* registered save room (0,14) */
 if(R8(0x020004EE)>1)return; /* tested idle/jump (0) and attack (1) only */
 if(R8(0x0201331C)&15u)return;
 /* Native screen X is signed 16.16; camera X is signed pixels. */
 s32 camera=(short)R16(0x0200A09A);
 s32 x=(s32)R32(0x02000524);
 if(camera < -256 || camera > 256)return; /* bound fixed-point multiplication */
 s32 boundary=(80-camera)*65536;
 if(x<boundary){
  R32(0x02000524)=(u32)boundary;
  if((s32)R32(0x0200052C)<0)R32(0x0200052C)=0;
 }
}
