/*
 Navicat Premium Data Transfer

 Source Server         : localhost_mysql_8.0
 Source Server Type    : MySQL
 Source Server Version : 80039
 Source Host           : localhost:3306
 Source Schema         : crm-data-crawl

 Target Server Type    : MySQL
 Target Server Version : 80039
 File Encoding         : 65001

 Date: 26/07/2024 18:04:06
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for tiktok_creator_user_info
-- ----------------------------
DROP TABLE IF EXISTS `tiktok_creator_user_info`;
CREATE TABLE `tiktok_creator_user_info`  (
  `user_id` bigint NOT NULL COMMENT 'user_id',
  `creator_oecuid` bigint NOT NULL COMMENT '创造者id',
  `is_authorized` int NULL DEFAULT NULL COMMENT '是否授权',
  `unique_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'unique_id',
  `units_sold_range` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '售出商品 数量',
  `selection_region` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `med_gmv_revenue_range` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'GMV 商品交易总额',
  `creator_bind_mcn_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'MCN',
  `industry_groups` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '创作者标签',
  `top_follower_gender` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '粉丝性别和百分比',
  `top_follower_ages` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '粉丝年龄 多年龄段',
  `follower_cnt` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '粉丝数量',
  `top_follower_age` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '粉丝年龄 主要',
  `video_avg_view_cnt` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频平均观看次数',
  PRIMARY KEY (`user_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tiktok_user_info
-- ----------------------------
DROP TABLE IF EXISTS `tiktok_user_info`;
CREATE TABLE `tiktok_user_info`  (
  `id` bigint NOT NULL COMMENT 'tiktok_user_id',
  `unique_id` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'tiktok_unique_id',
  `nickname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户名称',
  `avatar_larger` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用户头像',
  `avatar_medium` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用户头像(大分辨率)',
  `avatar_thumb` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用户头像(小分辨率)',
  `signature` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '签名',
  `region` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '国家',
  `sec_uid` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `bio_link` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '挂载链接',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tiktok_user_stats
-- ----------------------------
DROP TABLE IF EXISTS `tiktok_user_stats`;
CREATE TABLE `tiktok_user_stats`  (
  `user_id` bigint NOT NULL COMMENT 'tiktok主键User Id',
  `follower_count` int NULL DEFAULT NULL COMMENT '粉丝数',
  `following_count` int NULL DEFAULT NULL COMMENT '关注数量',
  `heart` int NULL DEFAULT NULL COMMENT '点赞数(主要)',
  `heart_count` int NULL DEFAULT NULL COMMENT '点赞数',
  `video_count` int NULL DEFAULT NULL COMMENT '视频数',
  `digg_count` int NULL DEFAULT NULL,
  `friend_count` int NULL DEFAULT NULL COMMENT '朋友数',
  PRIMARY KEY (`user_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
