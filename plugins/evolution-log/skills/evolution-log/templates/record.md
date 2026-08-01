---
id: YYYY-MM-DD-slug-here
date: YYYY-MM-DD
type: solution_change        # solution_change | requirement_change | migration | decision
title: 一句话标题
from: 变更前的一句话概括
to: 变更后的一句话概括
owner: 牵头人姓名
participants: []
status: draft                # draft | confirmed | superseded
source: manual               # manual | auto_hook
supersedes: []               # 被本次变更推翻的旧记录 id 列表
related: []                  # 弱关联记录 id 列表
tags: []
commits: []                  # 关联代码提交(可选)
---

## 背景

(变更发生前的状态,为什么原方案当初是合理的)

## 变更原因

(触发变更的直接原因:性能瓶颈 / 需求变化 / 安全事件 / 依赖淘汰…)

## 被否掉的备选方案

(考虑过但没选的路,以及为什么没选——这是最容易丢失、最有价值的信息)

## 影响范围

(受影响的模块、接口、团队,以及迁移成本)

## 决策过程

(谁在什么场合拍板,是否有争议,争议点是什么)
