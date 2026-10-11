/* Original exact-ROM native SDK. Explicit state, no libc/startup/global BSS. */
#ifndef DOMINANCE_H
#define DOMINANCE_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int s32;
#define R8(a) (*(volatile u8 *)(a))
#define R16(a) (*(volatile u16 *)(a))
#define R32(a) (*(volatile u32 *)(a))
#define ABI 1u
#define STATE_MAGIC 0x444D4142u
#define CONFIG_MAGIC 0x444D4346u
#define STATE ((volatile Shared *)0x0203D000)
#define REGEN ((volatile RegenState *)0x0203D040)
#define FOCUS ((volatile FocusState *)0x0203D050)
#define CONFIG ((const Config *)0x0867F000)
#define KEY_R 0x100u
#define DIR_KEYS 0xF0u
/* All fields are 32-bit in shared header; fixed offsets are documented. */
typedef struct {u32 magic,abi,tag,room,ticks,active_frames,resets,active,previous_held,block_reason,reserved[6];} Shared;
typedef struct {u32 timer,events,reserved[2];} RegenState;
typedef struct {u32 cooldown,events,reserved[2];} FocusState;
typedef struct {u32 magic,abi,mask,tag,regen_interval,regen_amount,focus_button,focus_amount,focus_cost,focus_cooldown;} Config;
typedef struct {u32 room,held,pressed,released;u16 hp,mp,max_hp,max_mp; s32 vx,vy;u8 player_state;} Context;
_Static_assert(sizeof(Shared)==64,"Shared ABI drift");
_Static_assert(sizeof(RegenState)==16 && sizeof(FocusState)==16,"Feature ABI drift");
_Static_assert(sizeof(Config)==40,"Config ABI drift");
static void clear_words(volatile u32 *p,u32 count){while(count--)*p++=0;}
static u16 capped_add(u16 value,u16 cap,u32 amount){u32 result=value+amount;return (u16)(result>cap?cap:result);}
static u32 blocked(void){
 if(CONFIG->magic!=CONFIG_MAGIC || CONFIG->abi!=ABI)return 1;
 if(R8(0x02000010)!=4)return 2;
 if(R8(0x02000064)!=1)return 3;
 if(R8(0x02013266)!=0)return 4; /* Soma only */
 if(R16(0x0201327A)==0)return 5;
 if(R8(0x020004EE)!=0)return 6; /* Conservative: skip attacks/hurt/events/transforms. */
 if(R32(0x02000088)<0x08000000 || R32(0x02000088)>=0x08800000)return 7;
 if(R32(0x0200042C)&1u)return 9; /* Observed native save-prompt lock; no broader flag semantics claimed. */
 if(R16(0x0201327E)==0 || R16(0x0201327A)>R16(0x0201327E) || R16(0x0201327C)>R16(0x02013280))return 8;
 return 0;
}
static Context context(u32 held,u32 previous){
 Context c;c.room=R32(0x02000088);c.held=held;c.pressed=held&~previous;c.released=previous&~held;
 c.hp=R16(0x0201327A);c.mp=R16(0x0201327C);c.max_hp=R16(0x0201327E);c.max_mp=R16(0x02013280);
 c.vx=(s32)R32(0x0200052C);c.vy=(s32)R32(0x02000530);c.player_state=R8(0x020004EE);return c;
}
#endif
