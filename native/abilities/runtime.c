/* One after-update dispatcher, explicit RAM ABI, deterministic feature order. */
#include "dominance.h"
#include "features.h"
typedef void (*FeatureTick)(const Context *);
typedef struct {u32 mask;volatile u32 *ram;u32 words;FeatureTick tick;} Feature;
/* Registration order is dispatch order; modules own disjoint explicit RAM. */
static const Feature features[]={
 {2,(volatile u32 *)FOCUS,4,focus_heal},
 {1,(volatile u32 *)REGEN,4,still_regen}
};
#define FEATURE_COUNT (sizeof(features)/sizeof(features[0]))
static void reset_features(void){
 for(u32 i=0;i<FEATURE_COUNT;i++)clear_words(features[i].ram,features[i].words);
 STATE->resets++;
}
__attribute__((section(".text.tick"))) void tick(void){
 u32 held=R16(0x02000014),reason=blocked();
 if(STATE->magic!=STATE_MAGIC || STATE->abi!=ABI || STATE->tag!=CONFIG->tag){
  clear_words((volatile u32 *)STATE,16);reset_features();STATE->magic=STATE_MAGIC;STATE->abi=ABI;STATE->tag=CONFIG->tag;STATE->previous_held=held;
 }
 STATE->ticks++;STATE->block_reason=reason;
 u32 room=R32(0x02000088);
 if(R8(0x02000010)==4 && room>=0x08000000 && room<0x08800000 && STATE->room!=room){reset_features();STATE->room=room;STATE->previous_held=held;}
 if(reason){
  REGEN->timer=0;STATE->active=0;STATE->previous_held=held;
  /* Pause freezes focus cooldown. Death/non-gameplay clears all feature state. */
  if((R8(0x02000010)!=4 || R16(0x0201327A)==0) && STATE->room){reset_features();STATE->room=0;}
  return;
 }

 if(!STATE->active)STATE->previous_held=held; /* No synthetic edge on resume. */
 Context c=context(held,STATE->previous_held);STATE->previous_held=held;STATE->active=1;STATE->active_frames++;
 /* Input action first; refresh snapshot before passive regen to avoid stale HP. */
 for(u32 i=0;i<FEATURE_COUNT;i++){
  if(CONFIG->mask&features[i].mask)features[i].tick(&c);
  c.hp=R16(0x0201327A);c.mp=R16(0x0201327C);
 }
}
