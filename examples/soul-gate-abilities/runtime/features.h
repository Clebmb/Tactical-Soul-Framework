/* Two independent feature modules. All native writes are gated by dispatcher. */
#ifndef FEATURES_H
#define FEATURES_H
static void still_regen(const Context *c){
 if(c->vx || c->vy || (c->held&DIR_KEYS) || c->hp>=c->max_hp){REGEN->timer=0;return;}
 if(++REGEN->timer>=CONFIG->regen_interval){
  REGEN->timer=0;R16(0x0201327A)=capped_add(c->hp,c->max_hp,CONFIG->regen_amount);REGEN->events++;
 }
}
static void focus_heal(const Context *c){
 if(FOCUS->cooldown)FOCUS->cooldown--;
 if(!(c->pressed&CONFIG->focus_button) || FOCUS->cooldown || c->hp>=c->max_hp || c->mp<CONFIG->focus_cost)return;
 R16(0x0201327A)=capped_add(c->hp,c->max_hp,CONFIG->focus_amount);
 R16(0x0201327C)=(u16)(c->mp-CONFIG->focus_cost);FOCUS->cooldown=CONFIG->focus_cooldown;FOCUS->events++;
}
#endif
