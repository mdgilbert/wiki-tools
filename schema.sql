-- MySQL dump 10.13  Distrib 5.5.41, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: reflex_relations_2014
-- ------------------------------------------------------
-- Server version	5.5.41-0ubuntu0.12.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `geo_asn`
--

DROP TABLE IF EXISTS `geo_asn`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `geo_asn` (
  `ga_start_ip` varbinary(10) NOT NULL,
  `ga_end_ip` varbinary(10) NOT NULL,
  `ga_name` varbinary(512) NOT NULL,
  `dummy` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`ga_start_ip`,`ga_end_ip`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `geo_blocks`
--

DROP TABLE IF EXISTS `geo_blocks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `geo_blocks` (
  `gb_start_ip` varbinary(15) NOT NULL DEFAULT '0',
  `gb_end_ip` varbinary(15) NOT NULL DEFAULT '0',
  `gb_start_block` int(10) unsigned NOT NULL DEFAULT '0',
  `gb_end_block` int(10) unsigned NOT NULL DEFAULT '0',
  `gb_id` int(10) unsigned NOT NULL,
  `dummy` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`gb_start_ip`,`gb_end_ip`),
  KEY `gb_id` (`gb_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `geo_location`
--

DROP TABLE IF EXISTS `geo_location`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `geo_location` (
  `gl_id` int(10) unsigned NOT NULL,
  `gl_country` varbinary(2) NOT NULL,
  `gl_region` varbinary(128) NOT NULL DEFAULT '',
  `gl_city` varbinary(128) NOT NULL DEFAULT '',
  `gl_postal_code` varbinary(10) NOT NULL DEFAULT '',
  `gl_lat` float(8,4) NOT NULL DEFAULT '0.0000',
  `gl_long` float(8,4) NOT NULL DEFAULT '0.0000',
  `gl_metro_code` varbinary(5) NOT NULL DEFAULT '',
  `gl_area_code` varbinary(5) NOT NULL DEFAULT '',
  `dummy` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`gl_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `index_history`
--

DROP TABLE IF EXISTS `index_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `index_history` (
  `h_index_type` varbinary(64) NOT NULL,
  `h_indexed` varbinary(255) NOT NULL,
  `h_completed` varbinary(14) DEFAULT NULL,
  PRIMARY KEY (`h_index_type`,`h_indexed`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `n_page_reverts`
--

DROP TABLE IF EXISTS `n_page_reverts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `n_page_reverts` (
  `pr_page_id` int(11) NOT NULL,
  `pr_revert_user` int(11) NOT NULL,
  `pr_revert_rev` int(8) unsigned NOT NULL,
  `pr_revert_timestamp` varbinary(14) NOT NULL,
  `pr_reverted_by_user` int(11) NOT NULL,
  `pr_reverted_by_rev` int(8) unsigned NOT NULL,
  `pr_reverted_by_timestamp` varbinary(14) NOT NULL,
  PRIMARY KEY (`pr_page_id`,`pr_revert_rev`,`pr_reverted_by_rev`),
  KEY `pr_revert_user` (`pr_revert_user`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `page_reverts`
--

DROP TABLE IF EXISTS `page_reverts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `page_reverts` (
  `pr_page_id` int(11) NOT NULL,
  `pr_revert_user` bigint(20) NOT NULL DEFAULT '0',
  `pr_revert_rev` int(8) unsigned NOT NULL,
  `pr_revert_timestamp` varbinary(14) NOT NULL,
  `pr_reverted_by_user` bigint(20) NOT NULL DEFAULT '0',
  `pr_reverted_by_rev` int(8) unsigned NOT NULL,
  `pr_reverted_by_timestamp` varbinary(14) NOT NULL,
  PRIMARY KEY (`pr_page_id`,`pr_revert_rev`,`pr_reverted_by_rev`),
  KEY `pr_revert_user` (`pr_revert_user`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project` (
  `p_id` int(11) NOT NULL,
  `p_title` varbinary(255) NOT NULL,
  `p_created` varbinary(14) DEFAULT NULL,
  `p_member_to` smallint(5) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`p_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_activity`
--

DROP TABLE IF EXISTS `project_activity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_activity` (
  `pa_project_id` int(8) NOT NULL,
  `pa_page_id` int(8) NOT NULL,
  `pa_page_namespace` smallint(6) NOT NULL,
  `pa_ww_from` smallint(5) unsigned NOT NULL,
  `pa_edits` mediumint(9) unsigned NOT NULL,
  PRIMARY KEY (`pa_project_id`,`pa_page_id`,`pa_ww_from`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_page_links_history`
--

DROP TABLE IF EXISTS `project_page_links_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_page_links_history` (
  `pplh_project_id` int(11) NOT NULL,
  `pplh_page_id` int(11) NOT NULL,
  `pplh_revision` int(11) NOT NULL,
  PRIMARY KEY (`pplh_project_id`,`pplh_page_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_pages`
--

DROP TABLE IF EXISTS `project_pages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_pages` (
  `pp_id` int(11) NOT NULL,
  `pp_project_id` int(11) NOT NULL,
  `pp_parent_category` varbinary(255) NOT NULL,
  `pp_parent_category_id` int(11) NOT NULL,
  PRIMARY KEY (`pp_id`,`pp_project_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_pages_assessments`
--

DROP TABLE IF EXISTS `project_pages_assessments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_pages_assessments` (
  `pa_id` int(11) NOT NULL DEFAULT '0',
  `pa_assessment` varbinary(255) NOT NULL,
  PRIMARY KEY (`pa_id`,`pa_assessment`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_template_links_history`
--

DROP TABLE IF EXISTS `project_template_links_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_template_links_history` (
  `ptlh_project_id` int(11) NOT NULL,
  `ptlh_page_id` int(11) NOT NULL,
  `ptlh_revision` int(11) NOT NULL,
  PRIMARY KEY (`ptlh_project_id`,`ptlh_page_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_user_links`
--

DROP TABLE IF EXISTS `project_user_links`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_user_links` (
  `pm_user_id` bigint(20) NOT NULL,
  `pm_user_name` varbinary(255) NOT NULL,
  `pm_link_rev` int(8) unsigned NOT NULL,
  `pm_link_date` varbinary(14) NOT NULL,
  `pm_link_removed` tinyint(1) NOT NULL,
  `pm_added_by` bigint(20) NOT NULL,
  `pm_added_by_name` varbinary(255) NOT NULL DEFAULT '',
  `pm_project_id` int(8) unsigned NOT NULL,
  `pm_page_id` int(8) unsigned NOT NULL,
  `pm_is_transclusion` tinyint(1) NOT NULL DEFAULT '0',
  KEY `pm_project_id` (`pm_project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reflex_cache`
--

DROP TABLE IF EXISTS `reflex_cache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reflex_cache` (
  `rc_user_id` bigint(20) NOT NULL,
  `rc_page_id` int(11) NOT NULL,
  `rc_page_namespace` int(11) NOT NULL,
  `rc_edits` mediumint(9) NOT NULL,
  `rc_wikiweek` smallint(6) NOT NULL,
  PRIMARY KEY (`rc_user_id`,`rc_page_id`,`rc_wikiweek`),
  KEY `rc_page_id` (`rc_page_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ts_pages`
--

DROP TABLE IF EXISTS `ts_pages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ts_pages` (
  `tp_id` int(8) NOT NULL DEFAULT '0',
  `tp_title` varbinary(255) NOT NULL DEFAULT '',
  `tp_namespace` int(11) NOT NULL DEFAULT '0',
  `tp_is_redirect` tinyint(1) NOT NULL DEFAULT '0',
  `tp_cached_to` smallint(5) unsigned NOT NULL DEFAULT '0',
  `tp_revert_to` smallint(5) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`tp_id`),
  KEY `tp_title` (`tp_title`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ts_users`
--

DROP TABLE IF EXISTS `ts_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ts_users` (
  `tu_id` bigint(20) NOT NULL DEFAULT '0',
  `tu_name` varbinary(255) NOT NULL DEFAULT '',
  `tu_registration` varbinary(14) DEFAULT NULL,
  `tu_aka` varbinary(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`tu_id`,`tu_name`),
  KEY `tu_name` (`tu_name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ts_users_block`
--

DROP TABLE IF EXISTS `ts_users_block`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ts_users_block` (
  `tub_name` varbinary(15) NOT NULL,
  `tub_block` int(10) unsigned NOT NULL,
  PRIMARY KEY (`tub_name`,`tub_block`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ts_users_groups`
--

DROP TABLE IF EXISTS `ts_users_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ts_users_groups` (
  `tug_uid` int(10) unsigned DEFAULT NULL,
  `tug_group` varbinary(128) DEFAULT NULL,
  KEY `tug_uid` (`tug_uid`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-04-02 15:05:25
