-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: bcms
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `appointment_services`
--

DROP TABLE IF EXISTS `appointment_services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `appointment_services` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `unit_price` decimal(10,2) NOT NULL,
  `appointment_id` bigint NOT NULL,
  `service_id` bigint NOT NULL,
  `specialist_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `appointment_services_appointment_id_40b96890_fk_appointments_id` (`appointment_id`),
  KEY `appointment_services_service_id_cf930aa0_fk_services_id` (`service_id`),
  KEY `appointment_services_specialist_id_3c65ebbf_fk_specialists_id` (`specialist_id`),
  CONSTRAINT `appointment_services_appointment_id_40b96890_fk_appointments_id` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`id`),
  CONSTRAINT `appointment_services_service_id_cf930aa0_fk_services_id` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`),
  CONSTRAINT `appointment_services_specialist_id_3c65ebbf_fk_specialists_id` FOREIGN KEY (`specialist_id`) REFERENCES `specialists` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `appointment_services`
--

LOCK TABLES `appointment_services` WRITE;
/*!40000 ALTER TABLE `appointment_services` DISABLE KEYS */;
/*!40000 ALTER TABLE `appointment_services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `appointments`
--

DROP TABLE IF EXISTS `appointments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `appointments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `start_time` time(6) NOT NULL,
  `end_time` time(6) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `total_price` decimal(10,2) NOT NULL,
  `walk_in_name` varchar(200) NOT NULL,
  `walk_in_phone` varchar(20) NOT NULL,
  `source` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `center_id` bigint NOT NULL,
  `client_id` bigint DEFAULT NULL,
  `package_id` bigint DEFAULT NULL,
  `specialist_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `appointments_specialist_id_41d566a5_fk_specialists_id` (`specialist_id`),
  KEY `appointment_center__38a218_idx` (`center_id`,`date`),
  KEY `appointment_center__e39509_idx` (`center_id`,`status`),
  KEY `appointment_center__7b146a_idx` (`center_id`,`date`,`status`),
  KEY `appointments_client_id_ed088e20_fk_clients_id` (`client_id`),
  KEY `appointments_package_id_75663bf7_fk_packages_id` (`package_id`),
  CONSTRAINT `appointments_center_id_e267b1c2_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `appointments_client_id_ed088e20_fk_clients_id` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`),
  CONSTRAINT `appointments_package_id_75663bf7_fk_packages_id` FOREIGN KEY (`package_id`) REFERENCES `packages` (`id`),
  CONSTRAINT `appointments_specialist_id_41d566a5_fk_specialists_id` FOREIGN KEY (`specialist_id`) REFERENCES `specialists` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `appointments`
--

LOCK TABLES `appointments` WRITE;
/*!40000 ALTER TABLE `appointments` DISABLE KEYS */;
/*!40000 ALTER TABLE `appointments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=105 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add نوع المركز',6,'add_servicetype'),(22,'Can change نوع المركز',6,'change_servicetype'),(23,'Can delete نوع المركز',6,'delete_servicetype'),(24,'Can view نوع المركز',6,'view_servicetype'),(25,'Can add مركز',7,'add_center'),(26,'Can change مركز',7,'change_center'),(27,'Can delete مركز',7,'delete_center'),(28,'Can view مركز',7,'view_center'),(29,'Can add إعدادات',8,'add_settings'),(30,'Can change إعدادات',8,'change_settings'),(31,'Can delete إعدادات',8,'delete_settings'),(32,'Can view إعدادات',8,'view_settings'),(33,'Can add دور',9,'add_role'),(34,'Can change دور',9,'change_role'),(35,'Can delete دور',9,'delete_role'),(36,'Can view دور',9,'view_role'),(37,'Can add مستخدم',10,'add_user'),(38,'Can change مستخدم',10,'change_user'),(39,'Can delete مستخدم',10,'delete_user'),(40,'Can view مستخدم',10,'view_user'),(41,'Can add تصنيف',11,'add_servicecategory'),(42,'Can change تصنيف',11,'change_servicecategory'),(43,'Can delete تصنيف',11,'delete_servicecategory'),(44,'Can view تصنيف',11,'view_servicecategory'),(45,'Can add خدمة',12,'add_service'),(46,'Can change خدمة',12,'change_service'),(47,'Can delete خدمة',12,'delete_service'),(48,'Can view خدمة',12,'view_service'),(49,'Can add باقة',13,'add_package'),(50,'Can change باقة',13,'change_package'),(51,'Can delete باقة',13,'delete_package'),(52,'Can view باقة',13,'view_package'),(53,'Can add package service',14,'add_packageservice'),(54,'Can change package service',14,'change_packageservice'),(55,'Can delete package service',14,'delete_packageservice'),(56,'Can view package service',14,'view_packageservice'),(57,'Can add عميل',15,'add_client'),(58,'Can change عميل',15,'change_client'),(59,'Can delete عميل',15,'delete_client'),(60,'Can view عميل',15,'view_client'),(61,'Can add متخصص',16,'add_specialist'),(62,'Can change متخصص',16,'change_specialist'),(63,'Can delete متخصص',16,'delete_specialist'),(64,'Can view متخصص',16,'view_specialist'),(65,'Can add موعد',17,'add_appointment'),(66,'Can change موعد',17,'change_appointment'),(67,'Can delete موعد',17,'delete_appointment'),(68,'Can view موعد',17,'view_appointment'),(69,'Can add appointment service',18,'add_appointmentservice'),(70,'Can change appointment service',18,'change_appointmentservice'),(71,'Can delete appointment service',18,'delete_appointmentservice'),(72,'Can view appointment service',18,'view_appointmentservice'),(73,'Can add فاتورة',19,'add_invoice'),(74,'Can change فاتورة',19,'change_invoice'),(75,'Can delete فاتورة',19,'delete_invoice'),(76,'Can view فاتورة',19,'view_invoice'),(77,'Can add invoice line',20,'add_invoiceline'),(78,'Can change invoice line',20,'change_invoiceline'),(79,'Can delete invoice line',20,'delete_invoiceline'),(80,'Can view invoice line',20,'view_invoiceline'),(81,'Can add تصنيف منتج',21,'add_productcategory'),(82,'Can change تصنيف منتج',21,'change_productcategory'),(83,'Can delete تصنيف منتج',21,'delete_productcategory'),(84,'Can view تصنيف منتج',21,'view_productcategory'),(85,'Can add منتج',22,'add_product'),(86,'Can change منتج',22,'change_product'),(87,'Can delete منتج',22,'delete_product'),(88,'Can view منتج',22,'view_product'),(89,'Can add حركة مخزون',23,'add_stockmovement'),(90,'Can change حركة مخزون',23,'change_stockmovement'),(91,'Can delete حركة مخزون',23,'delete_stockmovement'),(92,'Can view حركة مخزون',23,'view_stockmovement'),(93,'Can add حجز إلكتروني',24,'add_onlinebooking'),(94,'Can change حجز إلكتروني',24,'change_onlinebooking'),(95,'Can delete حجز إلكتروني',24,'delete_onlinebooking'),(96,'Can view حجز إلكتروني',24,'view_onlinebooking'),(97,'Can add طلب متجر',25,'add_storeorder'),(98,'Can change طلب متجر',25,'change_storeorder'),(99,'Can delete طلب متجر',25,'delete_storeorder'),(100,'Can view طلب متجر',25,'view_storeorder'),(101,'Can add store order item',26,'add_storeorderitem'),(102,'Can change store order item',26,'change_storeorderitem'),(103,'Can delete store order item',26,'delete_storeorderitem'),(104,'Can view store order item',26,'view_storeorderitem');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `center_settings`
--

DROP TABLE IF EXISTS `center_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `center_settings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `invoice_color` varchar(7) NOT NULL,
  `invoice_prefix` varchar(10) NOT NULL,
  `invoice_next_number` int unsigned NOT NULL,
  `invoice_footer` longtext NOT NULL,
  `show_tax_on_invoice` tinyint(1) NOT NULL,
  `tax_percent` decimal(5,2) NOT NULL,
  `booking_enabled` tinyint(1) NOT NULL,
  `booking_advance_days` int NOT NULL,
  `slot_minutes` int NOT NULL,
  `work_start` time(6) DEFAULT NULL,
  `work_end` time(6) DEFAULT NULL,
  `store_enabled` tinyint(1) NOT NULL,
  `store_name` varchar(200) NOT NULL,
  `store_cover` varchar(100) DEFAULT NULL,
  `loyalty_enabled` tinyint(1) NOT NULL,
  `points_per_currency` int NOT NULL,
  `reminder_enabled` tinyint(1) NOT NULL,
  `reminder_hours_before` int NOT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `center_id` (`center_id`),
  CONSTRAINT `center_settings_center_id_eb4ae356_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `center_settings_chk_1` CHECK ((`invoice_next_number` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `center_settings`
--

LOCK TABLES `center_settings` WRITE;
/*!40000 ALTER TABLE `center_settings` DISABLE KEYS */;
INSERT INTO `center_settings` VALUES (1,'#ec4899','INV',1,'',0,0.00,1,30,30,NULL,NULL,0,'','',0,1,0,24,1);
/*!40000 ALTER TABLE `center_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `centers`
--

DROP TABLE IF EXISTS `centers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `centers` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `slug` varchar(200) NOT NULL,
  `logo` varchar(100) DEFAULT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `address` longtext NOT NULL,
  `city` varchar(100) NOT NULL,
  `country` varchar(100) NOT NULL,
  `plan` varchar(20) NOT NULL,
  `plan_start` date NOT NULL,
  `plan_expires` date DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_demo` tinyint(1) NOT NULL,
  `timezone` varchar(50) NOT NULL,
  `currency` varchar(3) NOT NULL,
  `language` varchar(10) NOT NULL,
  `max_staff` int NOT NULL,
  `max_users` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `service_type_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`),
  KEY `centers_service_type_id_be2fd8cd_fk_service_types_id` (`service_type_id`),
  CONSTRAINT `centers_service_type_id_be2fd8cd_fk_service_types_id` FOREIGN KEY (`service_type_id`) REFERENCES `service_types` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `centers`
--

LOCK TABLES `centers` WRITE;
/*!40000 ALTER TABLE `centers` DISABLE KEYS */;
INSERT INTO `centers` VALUES (1,'انجاز للخدمات','center','','0123456789','','','امدرمان','السودان','trial','2026-06-12',NULL,1,0,'Africa/Khartoum','SDG','ar',10,5,'2026-06-12 11:38:29.742284','2026-06-12 11:38:29.742297',1);
/*!40000 ALTER TABLE `centers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients`
--

DROP TABLE IF EXISTS `clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clients` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `gender` varchar(5) NOT NULL,
  `birthdate` date DEFAULT NULL,
  `notes` longtext NOT NULL,
  `referral` varchar(20) NOT NULL,
  `points` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `clients_center_id_phone_77554a52_uniq` (`center_id`,`phone`),
  CONSTRAINT `clients_center_id_b976d2fa_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients`
--

LOCK TABLES `clients` WRITE;
/*!40000 ALTER TABLE `clients` DISABLE KEYS */;
INSERT INTO `clients` VALUES (1,'خديحه','0123456789','','f',NULL,'','',0,1,'2026-06-12 11:39:09.378360','2026-06-12 11:39:09.378376',1),(4,'مها','0123456987','','f',NULL,'','',0,1,'2026-06-12 12:18:14.215911','2026-06-12 12:18:14.215929',1);
/*!40000 ALTER TABLE `clients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_users_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (9,'accounts','role'),(10,'accounts','user'),(1,'admin','logentry'),(17,'appointments','appointment'),(18,'appointments','appointmentservice'),(3,'auth','group'),(2,'auth','permission'),(19,'billing','invoice'),(20,'billing','invoiceline'),(15,'clients','client'),(4,'contenttypes','contenttype'),(7,'core','center'),(6,'core','servicetype'),(8,'core','settings'),(22,'products','product'),(21,'products','productcategory'),(23,'products','stockmovement'),(13,'services','package'),(14,'services','packageservice'),(12,'services','service'),(11,'services','servicecategory'),(5,'sessions','session'),(16,'staff','specialist'),(24,'store','onlinebooking'),(25,'store','storeorder'),(26,'store','storeorderitem');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'core','0001_initial','2026-06-11 20:32:20.370969'),(2,'contenttypes','0001_initial','2026-06-11 20:32:20.410246'),(3,'contenttypes','0002_remove_content_type_name','2026-06-11 20:32:20.493628'),(4,'auth','0001_initial','2026-06-11 20:32:20.771944'),(5,'auth','0002_alter_permission_name_max_length','2026-06-11 20:32:20.850225'),(6,'auth','0003_alter_user_email_max_length','2026-06-11 20:32:20.855501'),(7,'auth','0004_alter_user_username_opts','2026-06-11 20:32:20.860611'),(8,'auth','0005_alter_user_last_login_null','2026-06-11 20:32:20.866076'),(9,'auth','0006_require_contenttypes_0002','2026-06-11 20:32:20.869237'),(10,'auth','0007_alter_validators_add_error_messages','2026-06-11 20:32:20.874832'),(11,'auth','0008_alter_user_username_max_length','2026-06-11 20:32:20.880241'),(12,'auth','0009_alter_user_last_name_max_length','2026-06-11 20:32:20.885641'),(13,'auth','0010_alter_group_name_max_length','2026-06-11 20:32:20.902848'),(14,'auth','0011_update_proxy_permissions','2026-06-11 20:32:20.910863'),(15,'auth','0012_alter_user_first_name_max_length','2026-06-11 20:32:20.917152'),(16,'accounts','0001_initial','2026-06-11 20:32:21.418193'),(17,'admin','0001_initial','2026-06-11 20:32:21.549043'),(18,'admin','0002_logentry_remove_auto_add','2026-06-11 20:32:21.556519'),(19,'admin','0003_logentry_add_action_flag_choices','2026-06-11 20:32:21.563973'),(20,'services','0001_initial','2026-06-11 20:32:21.998482'),(21,'staff','0001_initial','2026-06-11 20:32:22.221311'),(22,'clients','0001_initial','2026-06-11 20:32:22.315290'),(23,'appointments','0001_initial','2026-06-11 20:32:22.905478'),(24,'products','0001_initial','2026-06-11 20:32:23.141457'),(25,'billing','0001_initial','2026-06-11 20:32:23.565710'),(26,'sessions','0001_initial','2026-06-11 20:32:23.600130'),(27,'store','0001_initial','2026-06-11 20:32:24.021759'),(28,'products','0002_stockmovement','2026-06-12 09:17:58.777311'),(29,'services','0002_alter_service_category','2026-06-12 09:17:58.941631'),(30,'billing','0002_alter_invoice_appointment','2026-06-12 12:14:58.414298');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('demwvit9ka1zduooriz7t8ylt2epead1','.eJxViz0OAiEQRu9CbQgw7gCW3sGaDDAEY8SNLJXx7mKyhXbfz3svEWhsNYzOz3DN4iS0OPxukdKN2_egde2SUnqMtnW5711eJtXozucd_LMr9TpVU8BhBMUla5PTkWJhNCprZ-3i2TmLvoACTH52A4nB4pI9eyxlBvH-ADyzNsI:1wY0rd:AJ-t7Q4-NBIrnZ4xpEyYce2752lkTAu4OKbj6qwzYZs','2026-07-12 12:19:57.314729');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoice_lines`
--

DROP TABLE IF EXISTS `invoice_lines`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoice_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `description` varchar(300) NOT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `discount_percent` decimal(5,2) NOT NULL,
  `line_total` decimal(10,2) NOT NULL,
  `invoice_id` bigint NOT NULL,
  `product_id` bigint DEFAULT NULL,
  `service_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `invoice_lines_invoice_id_9a48de71_fk_invoices_id` (`invoice_id`),
  KEY `invoice_lines_product_id_9635c047_fk_products_id` (`product_id`),
  KEY `invoice_lines_service_id_9cd0b614_fk_services_id` (`service_id`),
  CONSTRAINT `invoice_lines_invoice_id_9a48de71_fk_invoices_id` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`),
  CONSTRAINT `invoice_lines_product_id_9635c047_fk_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `invoice_lines_service_id_9cd0b614_fk_services_id` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoice_lines`
--

LOCK TABLES `invoice_lines` WRITE;
/*!40000 ALTER TABLE `invoice_lines` DISABLE KEYS */;
/*!40000 ALTER TABLE `invoice_lines` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoices`
--

DROP TABLE IF EXISTS `invoices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoices` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `number` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `discount_amount` decimal(10,2) NOT NULL,
  `tax_amount` decimal(10,2) NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `paid_amount` decimal(10,2) NOT NULL,
  `payment_method` varchar(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `appointment_id` bigint DEFAULT NULL,
  `center_id` bigint NOT NULL,
  `client_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `number` (`number`),
  UNIQUE KEY `appointment_id` (`appointment_id`),
  KEY `invoices_center_id_667a1323_fk_centers_id` (`center_id`),
  KEY `invoices_client_id_50ee676b_fk_clients_id` (`client_id`),
  CONSTRAINT `invoices_appointment_id_e7d080cd_fk_appointments_id` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`id`),
  CONSTRAINT `invoices_center_id_667a1323_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `invoices_client_id_50ee676b_fk_clients_id` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoices`
--

LOCK TABLES `invoices` WRITE;
/*!40000 ALTER TABLE `invoices` DISABLE KEYS */;
/*!40000 ALTER TABLE `invoices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `online_bookings`
--

DROP TABLE IF EXISTS `online_bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `online_bookings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `client_name` varchar(200) NOT NULL,
  `client_phone` varchar(20) NOT NULL,
  `client_email` varchar(254) NOT NULL,
  `preferred_date` date NOT NULL,
  `preferred_time` time(6) DEFAULT NULL,
  `notes` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `appointment_id` bigint DEFAULT NULL,
  `center_id` bigint NOT NULL,
  `service_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `appointment_id` (`appointment_id`),
  KEY `online_bookings_center_id_29edd0b6_fk_centers_id` (`center_id`),
  KEY `online_bookings_service_id_cfb3220d_fk_services_id` (`service_id`),
  CONSTRAINT `online_bookings_appointment_id_c3f0e617_fk_appointments_id` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`id`),
  CONSTRAINT `online_bookings_center_id_29edd0b6_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `online_bookings_service_id_cfb3220d_fk_services_id` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `online_bookings`
--

LOCK TABLES `online_bookings` WRITE;
/*!40000 ALTER TABLE `online_bookings` DISABLE KEYS */;
/*!40000 ALTER TABLE `online_bookings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `package_services`
--

DROP TABLE IF EXISTS `package_services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `package_services` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order` int unsigned NOT NULL,
  `package_id` bigint NOT NULL,
  `service_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `package_services_package_id_service_id_1bc10e26_uniq` (`package_id`,`service_id`),
  KEY `package_services_service_id_284d3375_fk_services_id` (`service_id`),
  CONSTRAINT `package_services_package_id_be923c58_fk_packages_id` FOREIGN KEY (`package_id`) REFERENCES `packages` (`id`),
  CONSTRAINT `package_services_service_id_284d3375_fk_services_id` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`),
  CONSTRAINT `package_services_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `package_services`
--

LOCK TABLES `package_services` WRITE;
/*!40000 ALTER TABLE `package_services` DISABLE KEYS */;
/*!40000 ALTER TABLE `package_services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `packages`
--

DROP TABLE IF EXISTS `packages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `packages` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `show_in_store` tinyint(1) NOT NULL,
  `image` varchar(100) DEFAULT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `packages_center_id_30b415a8_fk_centers_id` (`center_id`),
  CONSTRAINT `packages_center_id_30b415a8_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `packages`
--

LOCK TABLES `packages` WRITE;
/*!40000 ALTER TABLE `packages` DISABLE KEYS */;
/*!40000 ALTER TABLE `packages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_categories`
--

DROP TABLE IF EXISTS `product_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_categories` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `order` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `product_categories_center_id_0b0f45a4_fk_centers_id` (`center_id`),
  CONSTRAINT `product_categories_center_id_0b0f45a4_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `product_categories_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_categories`
--

LOCK TABLES `product_categories` WRITE;
/*!40000 ALTER TABLE `product_categories` DISABLE KEYS */;
INSERT INTO `product_categories` VALUES (1,'منتجات طبية',0,1,1),(2,'منتجات محلية',0,1,1);
/*!40000 ALTER TABLE `product_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `sku` varchar(100) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `cost` decimal(10,2) NOT NULL,
  `stock` decimal(10,2) NOT NULL,
  `min_stock` decimal(10,2) NOT NULL,
  `image` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `show_in_store` tinyint(1) NOT NULL,
  `category_id` bigint DEFAULT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `products_category_id_a7a3a156_fk_product_categories_id` (`category_id`),
  KEY `products_center_id_4a285ac5_fk_centers_id` (`center_id`),
  CONSTRAINT `products_category_id_a7a3a156_fk_product_categories_id` FOREIGN KEY (`category_id`) REFERENCES `product_categories` (`id`),
  CONSTRAINT `products_center_id_4a285ac5_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,'حنة الدامر','','',100.00,80.00,100.00,5.00,'',1,1,2,1),(2,'كريم طبي','','',50.00,35.00,100.00,5.00,'',1,1,1,1);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `permissions` json NOT NULL,
  `is_default` tinyint(1) NOT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `roles_center_id_name_433b42ba_uniq` (`center_id`,`name`),
  CONSTRAINT `roles_center_id_ddd60d6a_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `service_categories`
--

DROP TABLE IF EXISTS `service_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `service_categories` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `icon` varchar(60) NOT NULL,
  `color` varchar(7) NOT NULL,
  `order` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `service_categories_center_id_7d8ea07d_fk_centers_id` (`center_id`),
  CONSTRAINT `service_categories_center_id_7d8ea07d_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `service_categories_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `service_categories`
--

LOCK TABLES `service_categories` WRITE;
/*!40000 ALTER TABLE `service_categories` DISABLE KEYS */;
/*!40000 ALTER TABLE `service_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `service_types`
--

DROP TABLE IF EXISTS `service_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `service_types` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `icon` varchar(60) NOT NULL,
  `color` varchar(7) NOT NULL,
  `description` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `order` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `service_types_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `service_types`
--

LOCK TABLES `service_types` WRITE;
/*!40000 ALTER TABLE `service_types` DISABLE KEYS */;
INSERT INTO `service_types` VALUES (1,'عام','fas fa-spa','#ec4899','',1,0);
/*!40000 ALTER TABLE `service_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `services`
--

DROP TABLE IF EXISTS `services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `services` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `duration` int unsigned NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `cost` decimal(10,2) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `show_in_store` tinyint(1) NOT NULL,
  `order` int unsigned NOT NULL,
  `image` varchar(100) DEFAULT NULL,
  `category_id` bigint DEFAULT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `services_center_id_6ec44253_fk_centers_id` (`center_id`),
  KEY `services_category_id_a33744a9_fk_service_categories_id` (`category_id`),
  CONSTRAINT `services_category_id_a33744a9_fk_service_categories_id` FOREIGN KEY (`category_id`) REFERENCES `service_categories` (`id`),
  CONSTRAINT `services_center_id_6ec44253_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `services_chk_1` CHECK ((`duration` >= 0)),
  CONSTRAINT `services_chk_2` CHECK ((`order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `services`
--

LOCK TABLES `services` WRITE;
/*!40000 ALTER TABLE `services` DISABLE KEYS */;
INSERT INTO `services` VALUES (1,'حنه ساده','',60,100.00,0.00,1,1,0,'',NULL,1),(2,'حمام مغربي','',60,300.00,0.00,1,1,0,'',NULL,1),(3,'تنظيف بشرة','',60,300.00,0.00,1,1,0,'',NULL,1);
/*!40000 ALTER TABLE `services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `specialists`
--

DROP TABLE IF EXISTS `specialists`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `specialists` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `specialty` varchar(200) NOT NULL,
  `bio` longtext NOT NULL,
  `photo` varchar(100) DEFAULT NULL,
  `color` varchar(7) NOT NULL,
  `work_start` time(6) DEFAULT NULL,
  `work_end` time(6) DEFAULT NULL,
  `working_days` json NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `order` int unsigned NOT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `specialists_center_id_5f49f055_fk_centers_id` (`center_id`),
  CONSTRAINT `specialists_center_id_5f49f055_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `specialists_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `specialists`
--

LOCK TABLES `specialists` WRITE;
/*!40000 ALTER TABLE `specialists` DISABLE KEYS */;
INSERT INTO `specialists` VALUES (1,'سوسو','','مكياج','','','#6366f1','06:00:00.000000','16:00:00.000000','[]',1,0,1);
/*!40000 ALTER TABLE `specialists` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `specialists_services`
--

DROP TABLE IF EXISTS `specialists_services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `specialists_services` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `specialist_id` bigint NOT NULL,
  `service_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `specialists_services_specialist_id_service_id_8ca4633d_uniq` (`specialist_id`,`service_id`),
  KEY `specialists_services_service_id_716203d6_fk_services_id` (`service_id`),
  CONSTRAINT `specialists_services_service_id_716203d6_fk_services_id` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`),
  CONSTRAINT `specialists_services_specialist_id_f3878411_fk_specialists_id` FOREIGN KEY (`specialist_id`) REFERENCES `specialists` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `specialists_services`
--

LOCK TABLES `specialists_services` WRITE;
/*!40000 ALTER TABLE `specialists_services` DISABLE KEYS */;
INSERT INTO `specialists_services` VALUES (1,1,1),(2,1,3);
/*!40000 ALTER TABLE `specialists_services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_movements`
--

DROP TABLE IF EXISTS `stock_movements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_movements` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `change` decimal(12,2) NOT NULL,
  `type` varchar(20) NOT NULL,
  `reference` varchar(200) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `center_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `stock_movements_center_id_81727577_fk_centers_id` (`center_id`),
  KEY `stock_movements_product_id_5bacd6d9_fk_products_id` (`product_id`),
  CONSTRAINT `stock_movements_center_id_81727577_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `stock_movements_product_id_5bacd6d9_fk_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_movements`
--

LOCK TABLES `stock_movements` WRITE;
/*!40000 ALTER TABLE `stock_movements` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_movements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `store_order_items`
--

DROP TABLE IF EXISTS `store_order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `store_order_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `line_total` decimal(10,2) NOT NULL,
  `order_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `store_order_items_order_id_5f58ae14_fk_store_orders_id` (`order_id`),
  KEY `store_order_items_product_id_246da063_fk_products_id` (`product_id`),
  CONSTRAINT `store_order_items_order_id_5f58ae14_fk_store_orders_id` FOREIGN KEY (`order_id`) REFERENCES `store_orders` (`id`),
  CONSTRAINT `store_order_items_product_id_246da063_fk_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `store_order_items_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `store_order_items`
--

LOCK TABLES `store_order_items` WRITE;
/*!40000 ALTER TABLE `store_order_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `store_order_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `store_orders`
--

DROP TABLE IF EXISTS `store_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `store_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `client_name` varchar(200) NOT NULL,
  `client_phone` varchar(20) NOT NULL,
  `client_address` longtext NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `status` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `center_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `store_orders_center_id_652e867f_fk_centers_id` (`center_id`),
  CONSTRAINT `store_orders_center_id_652e867f_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `store_orders`
--

LOCK TABLES `store_orders` WRITE;
/*!40000 ALTER TABLE `store_orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `store_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `full_name` varchar(200) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `avatar` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_owner` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `last_login_at` datetime(6) DEFAULT NULL,
  `center_id` bigint DEFAULT NULL,
  `role_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `users_center_id_9db94a14_fk_centers_id` (`center_id`),
  KEY `users_role_id_1900a745_fk_roles_id` (`role_id`),
  CONSTRAINT `users_center_id_9db94a14_fk_centers_id` FOREIGN KEY (`center_id`) REFERENCES `centers` (`id`),
  CONSTRAINT `users_role_id_1900a745_fk_roles_id` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'pbkdf2_sha256$600000$X095055Nd8jLbHDw30eV3J$YubrxJjXIlF7OS571T+bByH+/gIXNirI1/Noyp5yHi8=','2026-06-12 11:38:30.044219',0,'khattab','انجاز للخدمات','','','',1,0,1,'2026-06-12 11:38:30.033301',NULL,1,NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_groups`
--

DROP TABLE IF EXISTS `users_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_groups_user_id_group_id_fc7788e8_uniq` (`user_id`,`group_id`),
  KEY `users_groups_group_id_2f3517aa_fk_auth_group_id` (`group_id`),
  CONSTRAINT `users_groups_group_id_2f3517aa_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `users_groups_user_id_f500bee5_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_groups`
--

LOCK TABLES `users_groups` WRITE;
/*!40000 ALTER TABLE `users_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_user_permissions`
--

DROP TABLE IF EXISTS `users_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_user_permissions_user_id_permission_id_3b86cbdf_uniq` (`user_id`,`permission_id`),
  KEY `users_user_permissio_permission_id_6d08dcd2_fk_auth_perm` (`permission_id`),
  CONSTRAINT `users_user_permissio_permission_id_6d08dcd2_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `users_user_permissions_user_id_92473840_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_user_permissions`
--

LOCK TABLES `users_user_permissions` WRITE;
/*!40000 ALTER TABLE `users_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-12 15:20:12
