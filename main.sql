/*
 Navicat Premium Data Transfer

 Source Server         : finanzas
 Source Server Type    : SQLite
 Source Server Version : 3035005 (3.35.5)
 Source Schema         : main

 Target Server Type    : SQLite
 Target Server Version : 3035005 (3.35.5)
 File Encoding         : 65001

 Date: 03/12/2024 15:19:01
*/

PRAGMA foreign_keys = false;

-- ----------------------------
-- Table structure for categorias
-- ----------------------------
DROP TABLE IF EXISTS "categorias";
CREATE TABLE "categorias" (
  "id_categoria" INTEGER PRIMARY KEY AUTOINCREMENT,
  "nombre_categoria" TEXT NOT NULL,
  "tipo" TEXT NOT NULL,
   (tipo IN ('Ingreso', 'Gasto'))
);

-- ----------------------------
-- Table structure for sqlite_sequence
-- ----------------------------
DROP TABLE IF EXISTS "sqlite_sequence";
CREATE TABLE "sqlite_sequence" (
  "name",
  "seq"
);

-- ----------------------------
-- Table structure for subcategorias
-- ----------------------------
DROP TABLE IF EXISTS "subcategorias";
CREATE TABLE "subcategorias" (
  "id_subcategoria" INTEGER PRIMARY KEY AUTOINCREMENT,
  "id_categoria" INTEGER NOT NULL,
  "nombre_subcategoria" TEXT NOT NULL,
  FOREIGN KEY ("id_categoria") REFERENCES "categorias" ("id_categoria") ON DELETE NO ACTION ON UPDATE NO ACTION
);

-- ----------------------------
-- Table structure for transacciones
-- ----------------------------
DROP TABLE IF EXISTS "transacciones";
CREATE TABLE "transacciones" (
  "id_transaccion" INTEGER PRIMARY KEY AUTOINCREMENT,
  "fecha" DATE NOT NULL,
  "tipo" TEXT NOT NULL,
  "monto" REAL NOT NULL,
  "id_subcategoria" INTEGER NOT NULL,
  "descripcion" TEXT,
  "id_usuario" INTEGER NOT NULL,
  FOREIGN KEY ("id_subcategoria") REFERENCES "subcategorias" ("id_subcategoria") ON DELETE NO ACTION ON UPDATE NO ACTION,
  FOREIGN KEY ("id_usuario") REFERENCES "usuarios" ("id_usuario") ON DELETE NO ACTION ON UPDATE NO ACTION,
   (tipo IN ('Ingreso', 'Gasto'))
);

-- ----------------------------
-- Table structure for usuarios
-- ----------------------------
DROP TABLE IF EXISTS "usuarios";
CREATE TABLE "usuarios" (
  "id_usuario" INTEGER PRIMARY KEY AUTOINCREMENT,
  "nombre" TEXT NOT NULL
);

-- ----------------------------
-- Auto increment value for categorias
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 17 WHERE name = 'categorias';

-- ----------------------------
-- Auto increment value for subcategorias
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 48 WHERE name = 'subcategorias';

-- ----------------------------
-- Auto increment value for usuarios
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 2 WHERE name = 'usuarios';

PRAGMA foreign_keys = true;
