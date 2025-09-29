/*
 Navicat Premium Dump SQL

 Source Server         : agentic_society
 Source Server Type    : SQLite
 Source Server Version : 3045000 (3.45.0)
 Source Schema         : main

 Target Server Type    : SQLite
 Target Server Version : 3045000 (3.45.0)
 File Encoding         : 65001

 Date: 22/03/2025 05:05:19
*/

PRAGMA foreign_keys = false;

-- ----------------------------
-- Table structure for question_set
-- ----------------------------
DROP TABLE IF EXISTS "question_set";
CREATE TABLE "question_set" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" TEXT,
  "description" TEXT
);

-- ----------------------------
-- Records of question_set
-- ----------------------------
INSERT INTO "question_set" VALUES (0, 'multi-choice', 'multi-choice');
INSERT INTO "question_set" VALUES (1, 'ipip_neo_120', 'ipip_neo_120');

-- ----------------------------
-- Auto increment value for question_set
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 1 WHERE name = 'question_set';

PRAGMA foreign_keys = true;
