# Dota2 Bot 调研

机器人不同的模式
> Team Level
>   Team Level Desires： PushLane， DefendLane， FarmLane， Roam， Roshan
> Mode Level
> Action Level

可以考虑的操作模式

> The list of valid bot modes to override are:
>     laning
>     attack
>     roam
>     retreat
>     secret_shop
>     side_shop
>     rune
>     push_tower_top
>     push_tower_mid
>     push_tower_bot
>     defend_tower_top
>     defend_tower_mid
>     defend_tower_bottom
>     assemble
>     team_roam
>     farm
>     defend_ally
>     evasive_maneuvers
>     roshan
>     item
>     ward

## 可以调用的API
### 全局函数
* 团队信息
    - 人员
    - 当前行动意愿
* 时间信息
* 单位位置信息
* 测算距离
* 

### 单位相关
* 行动优先级（清空队列，放入队列，始终保持）
* 移动
* 跟随
* 攻击（一次，持续）
* 指向施法
* 指定地点施法
* 购买
* 状态信息
    - 血量
    - 魔法
    - 移动速度
    - 伤害
    - 攻速
    - 攻击范围
    - 护甲
    - 魔免
    - 金钱
    - 位置
    - buff
        + 伤害提高，移动速度提高，防御护甲等等
        + 目盲，控制，缠绕，隐形，沉默，毒伤，眩晕，不能控制
    - 是否在持续施法
* 伤害信息
    - 当前帧承受伤害
    - 谁对谁，用什么造成了伤害
* 威胁等级（战斗力情况）


### 能力相关
* 技能伤害
* 范围
* 释放准备时间
* 需要的魔法
* 冷却时间
* 等级
* 主动被动
* 是否被激活
* 是否需要持续施法
* 施法距离
* 附加属性














