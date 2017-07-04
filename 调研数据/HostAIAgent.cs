using ACT;
//using Assets.Scripts.Common;
//using Assets.Scripts.Framework;
//using DataCenter;
//using FramwGameKernal;
//using Assets.Scripts.GameSystem;
using MobaGo.Sound;
using behaviac;
using MobaGo.FlatBuffer;
using System;
using System.Collections.Generic;
using UnityEngine;

using MobaGo.FrameSyncModule;
using MobaGo.Game.FrameSyncModule;
using MobaGo.Game.Network;
using MobaGo.Game;
using MobaGo.Game.DataCenter;

namespace MobaGo.Game
{
    [TypeMetaInfo("HostAIAgent", "具有Host能力的代理")]
    public class HostAIAgent : BTBaseAgent, IPooledMonoBehaviour, IActorComponent
    {
        public BaseCharLogic m_wrapper;//host

        public int m_frame = 0;
        private int m_dengerCoolTick = 30;
        private VecInt3 m_lastDest = VecInt3.zero;

        public virtual void OnCreate()
        {
        }

        public virtual void OnGet()
        {

        }

        public virtual void OnRecycle()
        {

        }

        public void Reset()
        {
            m_dengerCoolTick = 30;
            m_frame = 0;
        }

        public override int GetFrameRandom(uint maxNum)
        {
            return -1;
        }


        public virtual void Born(CCChar actor)
        {
            m_wrapper = actor.pCharCtrl;
            m_AgentFileName = "HostAI";
            base.SetCurAgentActive();
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取自己的ID", "")]
        #endif
        public uint GetMyObjID()
        {
            return m_wrapper.actor.ObjID;
        }

#if UNITY_EDITOR
        [MethodMetaInfo("判断自己是否在血战状态", "")]
#endif
        public bool IsBloodWarState()
        {
            return m_wrapper.enterBloodWarState;
        }

#if UNITY_EDITOR
        [MethodMetaInfo("播放Animation", "")]
        #endif
        public void PlayAnimation(string animationName, float blendTime, int layer, bool loop)
        {
//#if DEBUG_LOGOUT
//            if (MobaGo.Game.Data.DebugMask.HasMask(MobaGo.Game.Data.DebugMask.E_DBG_MASK.MASK_MOVEDATA))
//                DebugHelper.LogOut(string.Format("Playanim {0} : {1}", animationName, m_wrapper.myBehavior));
//#endif
#if UNITY_EDITOR
            m_wrapper.PlayAnimation(animationName, blendTime, layer, loop, 1f * CBattleSystem.instance.MoveSpeed);
#else
            m_wrapper.PlayAnimation(animationName, blendTime, layer, loop);
#endif
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否低智商AI", "是否低智商AI,条件是个人人机对战，个人的等级在5级以下的敌方电脑AI")]
        #endif
        public EBTStatus IsLowAI()
        {
            //CRoleInfo masterRoleInfo = CRoleInfoManager.instance.GetMasterRoleInfo();
            //if (masterRoleInfo.PvpLevel > 5u)
            //{
            //    return EBTStatus.BT_FAILURE;
            //}
            //List<Player> allPlayers = CPlayerManager.instance.GetAllPlayers();
            //int num = 0;
            //for (int i = 0; i < allPlayers.Count; i++)
            //{
            //    if (!allPlayers[i].Computer)
            //    {
            //        num++;
            //        if (num > 1)
            //        {
            //            return EBTStatus.BT_FAILURE;
            //        }
            //    }
            //}
            //Player hostPlayer = CPlayerManager.instance.GetHostPlayer();
            //if (!CPlayerManager.instance.IsAtSameCamp(hostPlayer.PlayerId, m_wrapper.actor.pCharMeta.PlayerId))
            //{
            //    return EBTStatus.BT_SUCCESS;
            //}
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("地图AI模式", "地图AI模式")]
        #endif
        public RES_LEVEL_HEROAITYPE GetMapAIMode()
        {
            ///fixlater by sun
            return RES_LEVEL_HEROAITYPE.RES_LEVEL_HEROAITYPE_FREEDOM;

            //             SLevelContext curLvelContext = BattleLogic.instance.GetCurLvelContext();
            //             return curLvelContext.AIModeType;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取Host当前的行为", "")]
        #endif
        public eObjBehavMode GetCurBehaviorMode()
        {
            return m_wrapper.myBehavior;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取视野范围", "")]
        #endif
        public int GetSightScope()
        {
            return m_wrapper.actor.pPropertyCtrl.aPropertys[RES_FUNCEFT_TYPE.RES_FUNCEFT_SightArea].totalValue;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("重置寻路路径", "设置寻路路点从第一个开始")]
        #endif
        public EBTStatus ResetRouteStartPoint()
        {
            if (m_wrapper.m_curWaypointsHolder == null || m_wrapper.m_curWaypointsHolder.startPoint == null || m_wrapper.m_curWaypointTarget.transform == null)
            {
                return EBTStatus.BT_SUCCESS;
            }
            m_wrapper.m_curWaypointTarget = m_wrapper.m_curWaypointsHolder.startPoint;
            m_wrapper.m_curWaypointTargetPosition = new VecInt3(m_wrapper.m_curWaypointTarget.transform.position);
            return EBTStatus.BT_SUCCESS;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("根据在阵营中的位置选择一条兵线", "根据在阵营中的位置选择一条兵线")]
        #endif
        public EBTStatus SelectRouteBySelfCampIndex()
        {
            ICharDataBase actorDataProvider = CharDataCenter.instance.GetCharDataProvider(CharDataDb.ServerDataDb);
            CUtilList<WaypointsHolder> waypointsList = BattleLogic.instance.mapLogic.GetWaypointsList(m_wrapper.actor.pCharMeta.ActorCamp);
            if (!DebugRobot.instance.OnePath)
            {
                CharServerData CharServerData = default(CharServerData);
                actorDataProvider.GetCharServerData(ref m_wrapper.actor.pCharMeta, ref CharServerData);
                int num = CharServerData.TheExtraInfo.BornPointIndex;

                if (waypointsList == null || waypointsList.Count == 0)
                {
                    return EBTStatus.BT_INVALID;
                }
                if (num < 0)
                {
                    return EBTStatus.BT_INVALID;
                }
                for (int i = 0; i < waypointsList.Count; i++)
                {
                    if (!(waypointsList[i] == null))
                    {
                        if (waypointsList[i].m_index == num)
                        {
                            m_wrapper.m_curWaypointsHolder = waypointsList[i];
                            m_wrapper.m_curWaypointTarget = m_wrapper.m_curWaypointsHolder.startPoint;
                            m_wrapper.m_curWaypointTargetPosition = new VecInt3(m_wrapper.m_curWaypointTarget.transform.position);
                            return EBTStatus.BT_SUCCESS;
                        }
                    }
                }
                num %= waypointsList.Count;
                m_wrapper.m_curWaypointsHolder = waypointsList[num];
                m_wrapper.m_curWaypointTarget = m_wrapper.m_curWaypointsHolder.startPoint;
                m_wrapper.m_curWaypointTargetPosition = new VecInt3(m_wrapper.m_curWaypointTarget.transform.position);
                return EBTStatus.BT_SUCCESS;
            }
            else
            {
                m_wrapper.m_curWaypointsHolder = waypointsList[0];
                m_wrapper.m_curWaypointTarget = m_wrapper.m_curWaypointsHolder.startPoint;
                m_wrapper.m_curWaypointTargetPosition = new VecInt3(m_wrapper.m_curWaypointTarget.transform.position);
                return EBTStatus.BT_SUCCESS;
            }

        }

        #if UNITY_EDITOR
        [MethodMetaInfo("选择离自己最近的一条兵线", "选择离自己最近的一条兵线")]
        #endif
        public EBTStatus SelectNearestRoute()
        {
            if (Singleton<BattleLogic>.GetInstance() == null || BattleLogic.instance.mapLogic == null)
            {
                return EBTStatus.BT_FAILURE;
            }
            CUtilList<WaypointsHolder> waypointsList = BattleLogic.instance.mapLogic.GetWaypointsList(m_wrapper.actor.pCharMeta.ActorCamp);
            if (waypointsList == null || waypointsList.Count == 0)
            {
                return EBTStatus.BT_FAILURE;
            }
            long num = long.MaxValue;
            WaypointsHolder waypointsHolder = null;
            for (int i = 0; i < waypointsList.Count; i++)
            {
                VecInt3 vInt = new VecInt3(waypointsList[i].startPoint.transform.position);
                long sqrMagnitudeLong2D = (m_wrapper.actorLocation - vInt).sqrMagnitudeLong2D;
                if (sqrMagnitudeLong2D < num)
                {
                    waypointsHolder = waypointsList[i];
                    num = sqrMagnitudeLong2D;
                }
            }
            if (waypointsHolder == null)
            {
                return EBTStatus.BT_FAILURE;
            }
            m_wrapper.m_curWaypointsHolder = waypointsHolder;
            m_wrapper.m_curWaypointTarget = m_wrapper.m_curWaypointsHolder.startPoint;
            m_wrapper.m_curWaypointTargetPosition = new VecInt3(m_wrapper.m_curWaypointTarget.transform.position);
            return EBTStatus.BT_SUCCESS;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("选择一条兵线做路径", "随机选择一条兵线")]
        #endif
        public bool SelectRoute()
        {
            if (m_wrapper == null)
            {
                DebugHelper.Assert(false, "m_wrapper为空");
                return false;
            }
            if (BattleLogic.instance.mapLogic == null)
            {
                /*DebugHelper.Assert(false, "BattleLogic.GetInstance().mapLogic为空, GameState:{0}", new object[]
                {
                    GameFSM.instance.currentStateName
                });*/
                return false;
            }
            CUtilList<WaypointsHolder> waypointsList = BattleLogic.instance.mapLogic.GetWaypointsList(m_wrapper.actor.pCharMeta.ActorCamp);
            if (waypointsList == null || waypointsList.Count == 0)
            {
                return false;
            }
            int num = UnityEngine.Random.Range(0, 10000);//(int)FrameRandom.Random(10000u);
            num %= waypointsList.Count;
            if (waypointsList[num] == null)
            {
                DebugHelper.Assert(false, "routeList[index]为空");
                return false;
            }
            m_wrapper.m_curWaypointsHolder = waypointsList[num];
            m_wrapper.m_curWaypointTarget = m_wrapper.m_curWaypointsHolder.startPoint;
            m_wrapper.m_curWaypointTargetPosition = new VecInt3(m_wrapper.m_curWaypointTarget.transform.position);
            return true;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取当前路径最后的方向", "获取当前路径最后的方向")]
        #endif
        public Vector3 GetCurRouteLastForward()
        {
            if (m_wrapper.m_curWaypointsHolder == null || m_wrapper.m_curWaypointsHolder.wayPoints == null || m_wrapper.m_curWaypointsHolder.wayPoints.Length <= 1)
            {
                return Vector3.zero;
            }
            Waypoint endPoint = m_wrapper.m_curWaypointsHolder.endPoint;
            Waypoint waypoint = m_wrapper.m_curWaypointsHolder.wayPoints[m_wrapper.m_curWaypointsHolder.wayPoints.Length - 2];
            return endPoint.transform.position - waypoint.transform.position;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否已有路径", "是否有路径")]
        #endif
        public bool HasRoute()
        {
            return !(m_wrapper.m_curWaypointsHolder == null);
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取路径点中的当前点的位置", "前提是已设定好路径")]
        #endif
        public Vector3 GetRouteCurWaypointPos()
        {
            return m_wrapper.GetRouteCurWaypointPos().vec3;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取路径点中的当前点的位置,用于沿路径点返回", "前提是已设定好路径")]
        #endif
        public Vector3 GetRouteCurWaypointPosPre()
        {
            return m_wrapper.GetRouteCurWaypointPosPre().vec3;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("当前路径点是不是起始点", "当前路径点是不是起始点")]
        #endif
        public EBTStatus IsCurWayPointStartPoint()
        {
            if (m_wrapper.m_isStartPoint)
            {
                return EBTStatus.BT_SUCCESS;
            }
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("路径点中的当前点是否有效", "前提是已设定好路径")]
        #endif
        public bool IsCurWaypointValid()
        {
            return m_wrapper.IsCurWaypointValid();
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("当前路径点是不是最后一个路径点", "前提是已设定好路径")]
        #endif
        public bool IsCurWaypointEndPoint()
        {
            return m_wrapper.m_isCurWaypointEndPoint;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("使用技能Cmd", "RequestUseSkill")]
        #endif
        public void RequestUseSkill(eSkillSlotType slotType)
        {
            InputModel.instance.SendStopMove(null, false);
            if (slotType == eSkillSlotType.SLOT_SKILL_0)
            {
                CSkillButtonManager skillButtonManager = CBattleSystem.instance.GetSkillButtonManager();
                skillButtonManager.SendUseCommonAttack(0, 0u);
                skillButtonManager.SendUseCommonAttack(1, 0u);
            }
            else if (slotType == eSkillSlotType.SLOT_SKILL_4)
            {
                CSkillButtonManager skillButtonManager = CBattleSystem.instance.GetSkillButtonManager();
                skillButtonManager.RequestUseSkillSlot(slotType, 1);
            }
            else
            {
                SkillSlot slot = m_wrapper.actor.pSkillCtrl.GetSkillSlot(slotType);
                if (slot.SkillObj.AppointType == SkillRangeAppointType.Pos)
                {
                    slot.skillIndicator.SetRobotSkillUsePosition();
                }
                m_wrapper.actor.pSkillCtrl.RequestUseSkillSlot(slotType);
            }

            //             RealUseSkill(slotType);

        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否可以移动", "是否可以移动")]
        #endif
        public EBTStatus CanMove()
        {
            if (m_wrapper.GetNoAbilityFlag(eObjAbilityType.ObjAbility_Move))
            {
                return EBTStatus.BT_FAILURE;
            }
            return EBTStatus.BT_SUCCESS;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否有队友的血量小于指定的比率值", "是否有队友的血量小于指定的比率值")]
        #endif
        public bool HasMemberHpLessThan(int hpRate)
        {
            Player ownerPlayer = CharHelper.GetOwnerPlayer(ref m_wrapper.actorPtr);
            ReadonlyContext<CharHandle_t>.Enumerator enumerator = ownerPlayer.GetAllHeroes().GetEnumerator();
            while (enumerator.MoveNext())
            {
                CharHandle_t current = enumerator.Current;
                CCChar handle = current.handle;
                if (hpRate > handle.pPropertyCtrl.actorHp * 10000 / handle.pPropertyCtrl.actorHpTotal)
                {
                    return true;
                }
            }
            return false;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("移动向目标点CMD", "RequestMovePosition")]
        #endif
        public void RequestMovePosition(Vector3 dest)
        {
            //             RealMovePosition(dest);
            //             return;
            // 
            //             UnityEngine.Debug.Log(".................." + dest
            VecInt3 dest2 = new VecInt3(dest);
            if (m_lastDest != dest2 || m_wrapper.myBehavior != eObjBehavMode.Destination_Move)
            {
                m_lastDest = dest2;
                //VecInt3 vInt = dest2 - m_wrapper.actor.location;

                //if (vInt != VecInt3.zero)
                //{
                //    int num = (int)((double)(IntMath.atan2(-vInt.z, vInt.x).single * 180f) / 3.1416);
                //    DebugHelper.Assert(num < 32767 && num > -32768, "WARN: num < 32767 && num > -32768");
                //    int num2 = num - InputModel.instance.PreMoveDirection;
                //    if (num2 > 1 || num2 < -1 || InputModel.instance.FixtimeDirSndFrame > 30)
                //    {
                //        InputModel.instance.SendMoveDirection(num);
                //    }
                //}

                FrameCommand<MoveToPosCommand> frameCommand = FrameCommandFactory.CreateFrameCommand<MoveToPosCommand>();
                MGFrameCommand<MoveToPosCommand> final = SmartReferencePool.instance.Fetch<MGFrameCommand<MoveToPosCommand>>();
                Player ownerPlayer = CharHelper.GetOwnerPlayer(ref m_wrapper.actorPtr);
                frameCommand.playerID = ownerPlayer.PlayerId;
                frameCommand.cmdData.destPosition = dest2;

                final.SetFrameCommand(ref frameCommand);
                final.playerID = ownerPlayer.PlayerId;

                GameDefine.BattleNetHandler.WriteMsg(final);
            }
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("自己同指定位置目标的距离是否大于指定值", "")]
        #endif
        public bool IsDistanceToPosOutRange(Vector3 aimPos, int range)
        {
            VecInt3 vInt = new VecInt3(aimPos);
            long num = (long)range;
            return (m_wrapper.actorLocation - vInt).sqrMagnitudeLong2D > num * num;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("自己同指定位置目标的距离是否小于指定值", "")]
        #endif
        public bool IsDistanceToPosInRange(Vector3 aimPos, int range)
        {
            VecInt3 vInt = new VecInt3(aimPos);
            long num = (long)range;
            return (m_wrapper.actorLocation - vInt).sqrMagnitudeLong2D < num * num;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("终止当前的移动", "仅仅停止移动组件,不走了")]
        #endif
        public void TerminateMove()
        {
            InputModel.instance.SendStopMove(null, true);

            //m_wrapper.TerminateMove();
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("设定自己的朝向", "设定自己的朝向")]
        #endif
        public virtual void LookAtDirection(Vector3 dest)
        {
            //if (dest == Vector3.zero)
            //{
            //    return;
            //}
            //VecInt3 inDirection = new VecInt3(dest);
            //m_wrapper.actor.pMoveCtrl.SetRotate(inDirection, true);        

            VecInt3 vInt = new VecInt3(dest);
            if (vInt != VecInt3.zero)
            {
                int num = (int)((double)(IntMath.atan2(-vInt.z, vInt.x).single * 180f) / 3.1416);
                DebugHelper.Assert(num < 32767 && num > -32768, "WARN: num < 32767 && num > -32768");

                InputModel.instance.SendMoveDirection(num);
                InputModel.instance.SendStopMove(null, false);
            }
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否被当前持有者操控", "是否被当前持有者操控")]
        #endif
        public EBTStatus IsControlByHostPlayer()
        {
            if (CharHelper.IsHostCtrlActor(ref m_wrapper.actorPtr))
            {
                return EBTStatus.BT_SUCCESS;
            }
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("播放英雄动作声音", "播放英雄动作声音")]
        #endif
        public void PlayHeroActSound(eActType actType)
        {

            PlayHeroVoiceMgr.instance.PlayHeroVoiceByEActType(actType, m_wrapper.actorPtr);

        }

        #if UNITY_EDITOR
        [MethodMetaInfo("选择范围内的敌人", "选择范围内的敌人")]
        #endif
        public uint GetNearestEnemy(int srchR)
        {
            uint objid = 0;
            CCChar nearestEnemy = TargetSearcher.instance.GetNearestEnemy(m_wrapper.actor, srchR, 0u, true);
            if (nearestEnemy != null)
            {
                objid = nearestEnemy.ObjID;
            }
            // #if DEBUG_LOGOUT
            //             if (MobaGo.Game.Data.DebugMask.HasMask(MobaGo.Game.Data.DebugMask.E_DBG_MASK.MASK_MOVEDATA))
            //                 DebugHelper.LogOut("The id = " + m_wrapper.actorPtr.handle.ObjID + " targetid =  " + objid);
            // #endif
            return objid;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("判断目标是否可被攻击", "判断目标是否可被攻击,可被攻击的前提是活的,不是无敌的,不是一个阵营的")]
        #endif
        public bool IsTargetCanBeAttacked(uint objID)
        {
            CharHandle_t actor = GameCharMgr.instance.GetActor(objID);
            if (!actor)
            {
                m_wrapper.ClearTarget();
                return false;
            }
            bool flag = m_wrapper.CanAttack(actor) && actor.handle.VisibilityControl.IsVisibleFor(m_wrapper.actor.pCharMeta.ActorCamp);
            if (!flag)
            {
                m_wrapper.ClearTarget();
            }
            return flag;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取角色的类型", "英雄，怪物，还是建筑")]
        #endif
        public eCharTypeDef GetActorType(uint objID)
        {
            CharHandle_t actor = GameCharMgr.instance.GetActor(objID);
            if (!actor)
            {
                return eCharTypeDef.Invalid;
            }
            return actor.handle.pCharMeta.ActorType;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("设定技能", "")]
        #endif
        public EBTStatus SetSkill(eSkillSlotType InSlot)
        {
            bool flag = m_wrapper.SetSkill(InSlot, false);
            if (flag)
            {
                return EBTStatus.BT_SUCCESS;
            }
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否能使用技能", "是否能使用指定的技能")]
        #endif
        public EBTStatus CanUseSkill(eSkillSlotType InSlot)
        {
            bool flag = m_wrapper.CanUseSkill(InSlot);
            if (flag)
            {
                return EBTStatus.BT_SUCCESS;
            }
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取指定技能的攻击范围", "获取指定技能的攻击范围")]
        #endif
        public int GetSkillAttackRange(eSkillSlotType InSlot)
        {
            Skill skill = m_wrapper.GetSkill(InSlot);
            if (skill != null && skill.cfgData != null)
            {
                return skill.cfgData.iMaxAttackDistance;
            }
            return 0;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("检查技能是否能对该目标类型释放", "检查技能是否能对该目标类型释放")]
        #endif
        public EBTStatus CheckSkillFilter(eSkillSlotType InSlot, uint objID)
        {
            Skill skill = m_wrapper.GetSkill(InSlot);
            uint dwSkillTargetFilter = skill.cfgData.dwSkillTargetFilter;
            CharHandle_t actor = GameCharMgr.instance.GetActor(objID);
            if (((ulong)dwSkillTargetFilter & (ulong)(1L << (int)(actor.handle.pCharMeta.ActorType & (eCharTypeDef)31))) > 0uL)
            {
                return EBTStatus.BT_FAILURE;
            }
            return EBTStatus.BT_SUCCESS;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取技能目标规则", "获取技能目标规则")]
        #endif
        public SkillTargetRule GetSkillTargetRule(eSkillSlotType InSlot)
        {
            Skill skill = m_wrapper.GetSkill(InSlot);
            if (skill != null && skill.cfgData != null)
            {
                return (SkillTargetRule)skill.cfgData.dwSkillTargetRule;
            }
            return (SkillTargetRule)1;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("自己同指定Actor目标的距离是否大于指定值", "")]
        #endif
        public bool IsDistanceToActorOutRange(uint objID, int range)
        {
            CharHandle_t actor = GameCharMgr.instance.GetActor(objID);
            if (!actor)
            {
                return false;
            }
            CCChar handle = actor.handle;
            long num = (long)range;
            if (handle.CharInfo != null)
            {
                num += (long)handle.CharInfo.iCollisionSize.x;
            }
            return (m_wrapper.actorLocation - handle.location).sqrMagnitudeLong2D > num * num;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("自己同指定Actor目标的距离是否小于指定值", "")]
        #endif
        public bool IsDistanceToActorInRange(uint objID, int range)
        {
            CharHandle_t actor = GameCharMgr.instance.GetActor(objID);
            if (!actor)
            {
                return false;
            }
            CCChar handle = actor.handle;
            long num = (long)range;
            if (handle.CharInfo != null)
            {
                num += (long)handle.CharInfo.iCollisionSize.x;
            }
            return (m_wrapper.actorLocation - handle.location).sqrMagnitudeLong2D < num * num;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("设定目标", "")]
        #endif
        public void SelectTarget(uint objID)
        {
            //CharHandle_t actor = GameCharMgr.instance.GetActor(objID);
            //m_wrapper.SelectTarget(actor);
            NetLockAttackTarget.instance.SendLockAttackTarget(objID);
        }

        [MethodMetaInfo("获取低血量的队友", "HPRate是比例,10000表示1; InSlot技能槽位,用于过滤")]
        public uint GetLowHpFriendChar(int srchR, int HPRate, eSkillSlotType InSlot)
        {
            uint filter = 0u;
            Skill skill = m_wrapper.GetSkill(InSlot);
            if (skill != null && skill.cfgData != null)
            {
                filter = skill.cfgData.dwSkillTargetFilter;
            }
            CCChar lowHpTeamMember = TargetSearcher.instance.GetLowHpTeamMember(m_wrapper.actorPtr, srchR, HPRate, filter);
            if (lowHpTeamMember != null)
            {
                return lowHpTeamMember.ObjID;
            }
            return 0u;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("移动到Actor目标点CMD", "移动到Actor目标点")]
        #endif
        public virtual void RequestMoveToActor(uint objID)
        {
            //             RealMoveToActor(objID);
            //             return;

            CharHandle_t actor = GameCharMgr.instance.GetActor(objID);
            if (!actor)
            {
                return;
            }
            VecInt3 dest2 = actor.handle.location;
            if (m_lastDest != dest2)
            {
                m_lastDest = dest2;
                //VecInt3 vInt = dest2 - m_wrapper.actor.location;

                //if (vInt != VecInt3.zero)
                //{
                //    int num = (int)((double)(IntMath.atan2(-vInt.z, vInt.x).single * 180f) / 3.1416);
                //    DebugHelper.Assert(num < 32767 && num > -32768, "WARN: num < 32767 && num > -32768");
                //    int num2 = num - InputModel.instance.PreMoveDirection;
                //    if (num2 > 1 || num2 < -1 || InputModel.instance.FixtimeDirSndFrame > 30)
                //    {
                //        InputModel.instance.SendMoveDirection(num);
                //    }
                //}

                FrameCommand<MoveToPosCommand> frameCommand = FrameCommandFactory.CreateFrameCommand<MoveToPosCommand>();
                MGFrameCommand<MoveToPosCommand> final = SmartReferencePool.instance.Fetch<MGFrameCommand<MoveToPosCommand>>();
                Player ownerPlayer = CharHelper.GetOwnerPlayer(ref m_wrapper.actorPtr);
                frameCommand.playerID = ownerPlayer.PlayerId;
                frameCommand.cmdData.destPosition = dest2;

                final.SetFrameCommand(ref frameCommand);
                final.playerID = ownerPlayer.PlayerId;

                GameDefine.BattleNetHandler.WriteMsg(final);
            }
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("学习技能", "")]
        #endif
        public void LearnSkillCommand(eSkillSlotType slot)
        {
            int index = (int)slot;
            byte bSkillLvl = 0;
            if (m_wrapper.actor.pSkillCtrl != null && m_wrapper.actor.pSkillCtrl.SkillSlotArray[index] != null)
            {
                bSkillLvl = (byte)m_wrapper.actor.pSkillCtrl.SkillSlotArray[index].GetSkillLevel();
            }
            // only available skill point > 0 , send learn skill command
            if (m_wrapper.actor.pSkillCtrl.m_iSkillPoint > 0)
            {
                MGSendMsgHelper.SendLearnSkillCommand(m_wrapper.actorPtr, slot, bSkillLvl);
            }
        }


        #if UNITY_EDITOR
        [MethodMetaInfo("获取当前生命值比率", "10000表示满血")]
        #endif
        public int GetHPPercent()
        {
            return m_wrapper.actor.pPropertyCtrl.actorHp * 10000 / m_wrapper.actor.pPropertyCtrl.actorHpTotal;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否在一定范围内己方强于敌人", "是否在一定范围内己方强于敌人 strengthRate代表了对方强弱的比率,如0.8,表示是否强于对方血量的0.8")]
        #endif
        public EBTStatus IsNearbyFriendStrongThanEnemy(int srchR, int strengthRate)
        {
            ulong num = (ulong)((long)srchR * (long)srchR);
            List<CharHandle_t> heroChars = GameCharMgr.instance.HeroChars;
            int count = heroChars.Count;
            int sumCurHpSelfCamp = 0;
            int sumTotalHpSelfCamp = 0;
            int sumCurHpOtherCamp = 0;
            int sumTotalHpOtherCamp = 0;
            for (int i = 0; i < count; i++)
            {
                CCChar handle = heroChars[i].handle;
                ulong sqrMagnitudeLong2D = (ulong)(handle.location - m_wrapper.actor.location).sqrMagnitudeLong2D;
                if (sqrMagnitudeLong2D < num)
                {
                    if (m_wrapper.actor.IsSelfCamp(handle))
                    {
                        sumCurHpSelfCamp += handle.pPropertyCtrl.actorHp;
                        sumTotalHpSelfCamp += handle.pPropertyCtrl.actorHpTotal;
                    }
                    else
                    {
                        sumCurHpOtherCamp += handle.pPropertyCtrl.actorHp;
                        sumTotalHpOtherCamp += handle.pPropertyCtrl.actorHpTotal;
                    }
                }
            }
            if (sumCurHpOtherCamp == 0)
            {
                return EBTStatus.BT_SUCCESS;
            }
            if (sumCurHpSelfCamp * sumTotalHpOtherCamp * 10000 > sumCurHpOtherCamp * sumTotalHpSelfCamp * strengthRate)
            //(sumCurHpSelfCamp / sumTotalHpSelfCamp) / (sumTotalHpSelfCamp / sumTotalHpOtherCamp) > strengthRate / 10000
            {
                return EBTStatus.BT_SUCCESS;
            }
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取最近的回血点位置", "")]
        #endif
        public Vector3 GetRestoredHpPos()
        {
            Vector3 result = Vector3.zero;
            VecInt3 zero = VecInt3.zero;
            VecInt3 forward = VecInt3.forward;
            if (BattleLogic.instance.mapLogic.GetRevivePosDir(ref m_wrapper.actor.pCharMeta, true, out zero, out forward))
            {
                result = (Vector3)zero;
            }
            return result;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否有敌人在范围内", "是否有敌人在范围内")]
        #endif
        public EBTStatus HasEnemyInRange(int range)
        {
            ulong num = (ulong)((long)range * (long)range);
            List<CharHandle_t> gameChars = GameCharMgr.instance.GameChars;
            int count = gameChars.Count;
            for (int i = 0; i < count; i++)
            {
                CCChar handle = gameChars[i].handle;
                if (!m_wrapper.actor.IsSelfCamp(handle))
                {
                    MonsterLogic MonsterLogic = handle.AsMonster();
                    if (MonsterLogic != null)
                    {
                        ADTMonsterCfgInfo cfgInfo = MonsterLogic.cfgInfo;
                        if (cfgInfo != null && cfgInfo.bMonsterType == 2)
                        {
                            ObjAgent actorAgent = handle.pCharAgent;
                            if (actorAgent.GetCurBehavior() == eObjBehavMode.State_Idle || actorAgent.GetCurBehavior() == eObjBehavMode.State_Dead || actorAgent.GetCurBehavior() == eObjBehavMode.State_Null)
                            {
                                goto IL_E0;
                            }
                        }
                    }
                    ulong sqrMagnitudeLong2D = (ulong)(handle.location - m_wrapper.actor.location).sqrMagnitudeLong2D;
                    if (sqrMagnitudeLong2D < num)
                    {
                        return EBTStatus.BT_SUCCESS;
                    }
                }
            IL_E0: ;
            }
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取召唤师技能类型", "获取召唤师技能类型")]
        #endif
        public RES_SUMMONERSKILL_TYPE GetSummonerSkillType(eSkillSlotType InSlot)
        {
            Skill skill = m_wrapper.GetSkill(InSlot);
            if (skill != null && skill.cfgData != null)
            {
                return (RES_SUMMONERSKILL_TYPE)skill.cfgData.bSkillType;
            }
            return (RES_SUMMONERSKILL_TYPE)2;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("使用回城", "使用回城")]
        #endif
        public void UseGoHomeSkill()
        {
            //m_wrapper.UseGoHomeSkill();

            if (m_wrapper.IsDeadState)
            {
                return;
            }
            if (!m_wrapper.actor.pSkillCtrl.IsDisableSkillSlot(eSkillSlotType.SLOT_SKILL_6) && m_wrapper.actor.pSkillCtrl.CanUseSkill(eSkillSlotType.SLOT_SKILL_6))
            {
                Skill skill = m_wrapper.GetSkill(eSkillSlotType.SLOT_SKILL_6);
                if (skill != null && skill.cfgData != null && skill.cfgData.bSkillType == 1)
                {
                    Skill curUseSkill = m_wrapper.actor.pSkillCtrl.CurUseSkill;
                    if (curUseSkill != null && curUseSkill.SlotType == eSkillSlotType.SLOT_SKILL_6)
                    {
                        return;
                    }

                    m_wrapper.actor.pSkillCtrl.RequestUseSkillSlot(eSkillSlotType.SLOT_SKILL_6);
                }
            }
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否进入极危险区域", "是否越塔等")]
        #endif
        public EBTStatus IsOverTower()
        {
            if (IsInDanger())
            {
                return EBTStatus.BT_SUCCESS;
            }
            if (TargetSearcher.instance.HasCantAttackEnemyBuilding(m_wrapper.actor, 8000))
            {
                SetInDanger();
                return EBTStatus.BT_SUCCESS;
            }
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("当前技能是否能被打断", "前技能是否能被打断")]
        #endif
        public bool IsUseSkillCompletedOrCanAbort()
        {
            Skill curUseSkill = m_wrapper.actor.pSkillCtrl.CurUseSkill;
            if (curUseSkill == null)
            {
                return true;
            }
            return false;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("是否有塔在范围内，且塔下没有自己的小兵", "是否有塔在范围内，且塔下没有自己的小兵")]
        #endif
        public EBTStatus HasEnemyBuildingAndEnemyBuildingWillAttackSelf(int srchR)
        {
            if (TargetSearcher.instance.HasEnemyBuildingAndEnemyBuildingWillAttackSelf(m_wrapper.actor, srchR))
            {
                return EBTStatus.BT_SUCCESS;
            }
            return EBTStatus.BT_FAILURE;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("设置自己进入危险状态", "设置自己进入危险状态")]
        #endif
        public void SetInDanger(int frame)
        {
            m_dengerCoolTick = frame;
        }


        #if UNITY_EDITOR
        [MethodMetaInfo("获取范围内的敌人数量", "获取范围内的敌人数量")]
        #endif
        public int CountEnemyInRange(int srchR)
        {
            return TargetSearcher.instance.GetEnemyCountInRange(m_wrapper.actor, srchR);
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取范围内的敌人英雄数量", "获取范围内的敌人英雄数量")]
        #endif
        public int CountEnemyHeroInRange(int srchR)
        {
            return TargetSearcher.instance.GetEnemyHeroCountInRange(m_wrapper.actor, srchR);
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取范围内的友军数量,包含自己", "获取范围内的友军数量,包含自己")]
        #endif
        public int CountOurCampChar(int srchR)
        {
            int num = 1;
            List<CCChar> ourCampChars = TargetSearcher.instance.GetOurCampChars(m_wrapper.actor, srchR);
            if (ourCampChars != null)
            {
                return num + ourCampChars.Count;
            }
            return num;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取指定点周围的随机点", "获取指定点周围的随机点")]
        #endif
        public Vector3 GetRandomPointNearGivenPoint(Vector3 aimPos, int range)
        {
            int num = UnityEngine.Random.Range(0, range * 2) - range;//(int)FrameRandom.Random((uint)(range * 2)) - range;
            int num2 = UnityEngine.Random.Range(0, range * 2) - range;//(int)FrameRandom.Random((uint)(range * 2)) - range;
            Vector3 vector = new Vector3(aimPos.x + (float)num * 0.001f, aimPos.y, aimPos.z + (float)num2 * 0.001f);
            if (PathfindingUtility.IsValidTarget(m_wrapper.actor, new VecInt3(vector)))
            {
                return vector;
            }
            return aimPos;
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("获取一个本地随机整数", "获取一个随机整数")]
        #endif
        public int GetLocalRandomInt(uint maxNum)
        {
            return UnityEngine.Random.Range(0, (int)maxNum);
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("购买装备Cmd", "")]
        #endif
        public void RequestBuyEquip()
        {
            if (((uint)m_frame + m_wrapper.actor.ObjID) % 30 == 0)
            {
                //CBattleEquipSystem battleEquipSystem = (CBattleEquipSystem)CBattleSystem.instance.m_battleEquipSystem;
                //if (battleEquipSystem == null)
                //{
                //    return;
                //}
                m_wrapper.actor.pEquipCtrl.GetQuicklyBuyEquipList();
                {
                    for (int i = 0; i < m_wrapper.actor.pEquipCtrl.retlist.Length; i++)
                    {
                        if (m_wrapper.actor.pEquipCtrl.retlist[i] > 0)
                        {
                            FrameCommand<PlayerBuyEquipCommand> frameCommand = FrameCommandFactory.CreateFrameCommand<PlayerBuyEquipCommand>();
                            MGFrameCommand<PlayerBuyEquipCommand> cmd = SmartReferencePool.instance.Fetch<MGFrameCommand<PlayerBuyEquipCommand>>();
                            frameCommand.cmdData.m_equipID = m_wrapper.actor.pEquipCtrl.retlist[i];
                            cmd.SetFrameCommand(ref frameCommand);
                            cmd.playerID = CPlayerManager.instance.HostPlayerId;
                            GameDefine.BattleNetHandler.WriteMsg(cmd);
                            break;
                        }
                    }
                }
            }
        }

        #if UNITY_EDITOR
        [MethodMetaInfo("随机推荐装", "")]
        #endif
        public void RandomRecommendEquips()
        {
            //m_wrapper.actor.pEquipCtrl.RandomRecommendEquips();
        }

        public override void FrameUpdate(int delta)
        {
            if (m_isPaused)
            {
                return;
            }
            m_frame++;
            if (m_wrapper != null)
            {
                if (((uint)m_frame + m_wrapper.actor.ObjID) % 3 == 0)
                {
                    base.FrameUpdate(delta);
                }
            }
            if (m_dengerCoolTick > 0)
            {
                m_dengerCoolTick--;
            }
        }

        public bool IsInDanger()
        {
            return m_dengerCoolTick > 0;
        }

        public void SetInDanger()
        {
            if (FrameSyncService.instance.isActive)
            {
                m_dengerCoolTick = 30;
            }
            else
            {
                m_dengerCoolTick = 60;
            }
        }
    }
}
