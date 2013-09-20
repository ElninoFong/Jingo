-- phpMyAdmin SQL Dump
-- version 3.5.5
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: May 27, 2013 at 07:42 AM
-- Server version: 5.5.29
-- PHP Version: 5.4.10

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `Jingo_DB`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `addscheduleproc`(OUT ret_id INT,
							   IN g_start DATETIME,
							   IN g_end DATETIME,
							   IN g_repeat INT,
							   IN g_dow INT)
BEGIN
	INSERT INTO SCHEDULE (starttime, endtime, repeat_id, dayofweek) VALUES (g_start, g_end, g_repeat, g_dow);
	SELECT last_insert_id() INTO ret_id;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `recnotesproc`(IN g_stateid INT,
							   IN g_locid INT,
							   IN g_time DATETIME,
							   IN per_page INT)
BEGIN
	SELECT DISTINCT email, username, words, NOTE.created_at, note_id
	FROM USER, NOTE NATURAL JOIN TAGS_IN_NOTE NATURAL JOIN TAGS_IN_FILTER
	WHERE note_id IN (SELECT note_id AS N1
					  FROM NOTE NATURAL JOIN SCHEDULE
					  WHERE CASE repeat_id
      				        WHEN 0 THEN g_time BETWEEN starttime AND endtime
     				        WHEN 1 THEN TIME(g_time) BETWEEN TIME(starttime) AND TIME(endtime)
        				    WHEN 2 THEN (TIME(g_time) BETWEEN TIME(starttime) AND TIME(endtime) 
                                AND WEEKDAY(g_time) = dayofweek)
    						END)
		  AND note_id IN (SELECT note_id AS N2
						  FROM NOTE NATURAL JOIN LOCATION AS L1, LOCATION AS L2 
						  WHERE L2.location_id = g_locid 
						  		AND lat_lng_distance(L1.latitude, L1.longitude, L2.latitude, L2.longitude) <= radius)
		  AND filter_id IN (SELECT filter_id AS F1
							FROM STATE NATURAL JOIN FILTER
							WHERE state_id = g_stateid)
		  AND filter_id IN (SELECT filter_id AS F2
							FROM FILTER NATURAL JOIN SCHEDULE
							WHERE CASE repeat_id
								WHEN 0 THEN g_time BETWEEN starttime AND endtime
								WHEN 1 THEN TIME(g_time) BETWEEN TIME(starttime) AND TIME(endtime)
								WHEN 2 THEN (TIME(g_time) BETWEEN TIME(starttime) AND TIME(endtime) 
									AND WEEKDAY(g_time) = dayofweek)
	 	 						  END)
		  AND USER.uid = NOTE.uid
		  ORDER BY NOTE.created_at DESC LIMIT per_page;
END$$

--
-- Functions
--
CREATE DEFINER=`root`@`localhost` FUNCTION `lat_lng_distance`(lat1 FLOAT, lng1 FLOAT, lat2 FLOAT, lng2 FLOAT) RETURNS float
    DETERMINISTIC
BEGIN
        RETURN 1000 * 6371 * 2 * ASIN(SQRT(
            POWER(SIN((lat1 - abs(lat2)) * pi()/180 / 2),
            2) + COS(lat1 * pi()/180 ) * COS(abs(lat2) *
            pi()/180) * POWER(SIN((lng1 - lng2) *
            pi()/180 / 2), 2) ));
    END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `COMMENT`
--

CREATE TABLE `COMMENT` (
  `comment_id` int(11) NOT NULL AUTO_INCREMENT,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `uid` int(11) DEFAULT NULL,
  `note_id` int(11) DEFAULT NULL,
  `content` text,
  PRIMARY KEY (`comment_id`),
  KEY `COMMENT_ibfk_1` (`uid`),
  KEY `COMMENT_ibfk_2` (`note_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=7 ;

--
-- Dumping data for table `COMMENT`
--

INSERT INTO `COMMENT` (`comment_id`, `created_at`, `uid`, `note_id`, `content`) VALUES
(1, '2013-05-23 22:13:10', 13, 10, 'This is useful.'),
(3, '2013-05-23 22:18:18', 14, 10, 'Not bad.'),
(5, '2013-05-23 22:20:42', 14, 3, 'hello.'),
(6, '2013-05-24 00:52:26', 14, 9, 'I like this one.');

-- --------------------------------------------------------

--
-- Table structure for table `DAYOFWEEK`
--

CREATE TABLE `DAYOFWEEK` (
  `dow_id` int(1) NOT NULL DEFAULT '0',
  `dow_name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`dow_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `DAYOFWEEK`
--

INSERT INTO `DAYOFWEEK` (`dow_id`, `dow_name`) VALUES
(0, 'Monday'),
(1, 'Tuesday'),
(2, 'Wednesday'),
(3, 'Thursday'),
(4, 'Friday'),
(5, 'Saturday'),
(6, 'Sunday');

-- --------------------------------------------------------

--
-- Table structure for table `FILTER`
--

CREATE TABLE `FILTER` (
  `filter_id` int(11) NOT NULL AUTO_INCREMENT,
  `state_id` int(11) DEFAULT NULL,
  `location_id` int(11) DEFAULT NULL,
  `filter_radius` int(5) DEFAULT NULL,
  `schedule_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`filter_id`),
  KEY `FILTER_ibfk_1` (`state_id`),
  KEY `FILTER_ibfk_2` (`location_id`),
  KEY `FILTER_ibfk_3` (`schedule_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=9 ;

--
-- Dumping data for table `FILTER`
--

INSERT INTO `FILTER` (`filter_id`, `state_id`, `location_id`, `filter_radius`, `schedule_id`) VALUES
(1, 2, NULL, NULL, 7),
(2, 3, NULL, NULL, 8),
(3, 6, NULL, NULL, 10),
(4, 4, NULL, NULL, 12),
(5, 7, NULL, NULL, 13),
(6, 8, NULL, NULL, 14),
(7, 9, NULL, NULL, 17),
(8, 2, NULL, NULL, 20);

-- --------------------------------------------------------

--
-- Table structure for table `FRIENDSHIP`
--

CREATE TABLE `FRIENDSHIP` (
  `from_uid` int(11) NOT NULL DEFAULT '0',
  `to_uid` int(11) NOT NULL DEFAULT '0',
  `request_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `response_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `response_status` int(1) DEFAULT '0',
  PRIMARY KEY (`from_uid`,`to_uid`),
  KEY `FRIEND_ibfk_2` (`to_uid`),
  KEY `response_status` (`response_status`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `FRIENDSHIP`
--

INSERT INTO `FRIENDSHIP` (`from_uid`, `to_uid`, `request_time`, `response_time`, `response_status`) VALUES
(13, 14, '2013-05-24 17:30:40', '0000-00-00 00:00:00', 0),
(16, 13, '2013-05-23 20:27:11', '0000-00-00 00:00:00', 1),
(16, 14, '2013-05-23 20:27:11', '0000-00-00 00:00:00', 1);

-- --------------------------------------------------------

--
-- Table structure for table `LIKE`
--

CREATE TABLE `LIKE` (
  `like_id` int(11) NOT NULL AUTO_INCREMENT,
  `note_id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  PRIMARY KEY (`like_id`),
  KEY `note_id` (`note_id`),
  KEY `uid` (`uid`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=28 ;

--
-- Dumping data for table `LIKE`
--

INSERT INTO `LIKE` (`like_id`, `note_id`, `uid`) VALUES
(20, 4, 14),
(21, 9, 14),
(22, 3, 15),
(23, 4, 15),
(24, 9, 15),
(25, 10, 13),
(26, 11, 13),
(27, 9, 13);

-- --------------------------------------------------------

--
-- Table structure for table `LOCATION`
--

CREATE TABLE `LOCATION` (
  `location_id` int(11) NOT NULL AUTO_INCREMENT,
  `latitude` float(10,6) DEFAULT NULL,
  `longitude` float(10,6) DEFAULT NULL,
  `location_name` varchar(200) NOT NULL,
  PRIMARY KEY (`location_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=82 ;

--
-- Dumping data for table `LOCATION`
--

INSERT INTO `LOCATION` (`location_id`, `latitude`, `longitude`, `location_name`) VALUES
(4, 40.641136, -74.020020, '341 61st Street, Brooklyn, NY 11220, USA'),
(5, 40.640942, -74.019905, '349 61st Street, Brooklyn, NY 11220, USA'),
(6, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(7, 40.640884, -74.019951, '346 61st Street, Brooklyn, NY 11220, USA'),
(8, 40.640869, -74.019928, '346 61st Street, Brooklyn, NY 11220, USA'),
(9, 40.640877, -74.019920, '346 61st Street, Brooklyn, NY 11220, USA'),
(10, 40.640877, -74.019920, '346 61st Street, Brooklyn, NY 11220, USA'),
(11, 40.694073, -73.986931, 'Polytechnic Institute of New York University, 6 Metrotech Center, Brooklyn, NY 11201, USA'),
(12, 40.694073, -73.986931, 'Polytechnic Institute of New York University, 6 Metrotech Center, Brooklyn, NY 11201, USA'),
(13, 40.640839, -74.019913, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(14, 40.640839, -74.019913, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(15, 40.640839, -74.019913, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(16, 40.640839, -74.019913, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(17, 40.640839, -74.019913, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(18, 40.640839, -74.019913, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(19, 40.640846, -74.019928, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(20, 40.640858, -74.019928, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(21, 40.640858, -74.019928, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(22, 40.640858, -74.019928, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(23, 40.641655, -74.014145, 'Pioneer Supermarket'),
(24, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(25, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(26, 40.640854, -74.019913, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(27, 40.640858, -74.019897, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(28, 40.640854, -74.019890, '351-353 61st Street, Brooklyn, NY 11220, USA'),
(29, 40.640854, -74.019890, '351-353 61st Street, Brooklyn, NY 11220, USA'),
(30, 40.642014, -74.017563, 'Bravo Supermarkets'),
(31, 40.640865, -74.019920, '346 61st Street, Brooklyn, NY 11220, USA'),
(32, 40.640930, -74.019951, '346 61st Street, Brooklyn, NY 11220, USA'),
(33, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(34, 40.640903, -74.019943, '346 61st Street, Brooklyn, NY 11220, USA'),
(35, 40.640900, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(36, 40.640873, -74.019966, '346 61st Street, Brooklyn, NY 11220, USA'),
(37, 40.640907, -74.019913, '346 61st Street, Brooklyn, NY 11220, USA'),
(38, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(39, 35.861660, 104.195396, 'China'),
(40, 42.358433, -71.059776, 'Boston, MA, USA'),
(41, 40.640854, -74.019890, '351-353 61st Street, Brooklyn, NY 11220, USA'),
(42, 40.640854, -74.019890, '351-353 61st Street, Brooklyn, NY 11220, USA'),
(43, 40.640846, -74.019844, '351-353 61st Street, Brooklyn, NY 11220, USA'),
(44, 40.640846, -74.019844, '351-353 61st Street, Brooklyn, NY 11220, USA'),
(45, 40.640846, -74.019844, '351-353 61st Street, Brooklyn, NY 11220, USA'),
(46, 40.640949, -74.014244, 'George''s Restaurant'),
(47, 40.640865, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(48, 40.640865, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(49, 40.640865, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(50, 40.640865, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(51, 40.640865, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(52, 40.640865, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(53, 40.640846, -74.019905, '349-351 61st Street, Brooklyn, NY 11220, USA'),
(54, 40.640858, -74.019989, '346 61st Street, Brooklyn, NY 11220, USA'),
(55, 40.640858, -74.019989, '346 61st Street, Brooklyn, NY 11220, USA'),
(56, 40.640858, -74.019989, '346 61st Street, Brooklyn, NY 11220, USA'),
(57, 40.640858, -74.019989, '346 61st Street, Brooklyn, NY 11220, USA'),
(58, 40.640858, -74.019989, '346 61st Street, Brooklyn, NY 11220, USA'),
(59, 40.640873, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(60, 40.640873, -74.019936, '346 61st Street, Brooklyn, NY 11220, USA'),
(61, 42.358433, -71.059776, 'Boston, MA, USA'),
(62, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(63, 40.694340, -73.986206, '52-70 Lawrence Street, Polytechnic Institute of New York University, Brooklyn, NY 11201, USA'),
(64, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(65, 40.694359, -73.986191, '52-70 Lawrence Street, Polytechnic Institute of New York University, Brooklyn, NY 11201, USA'),
(66, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(67, 40.694389, -73.986221, '52-70 Lawrence Street, Polytechnic Institute of New York University, Brooklyn, NY 11201, USA'),
(68, 40.694027, -73.986076, '61-81 Lawrence Street, Brooklyn, NY 11201, USA'),
(69, 40.694027, -73.986076, '61-81 Lawrence Street, Brooklyn, NY 11201, USA'),
(70, 40.694027, -73.986076, '61-81 Lawrence Street, Brooklyn, NY 11201, USA'),
(71, 40.694790, -73.985939, '105 Johnson Street, Brooklyn, NY 11201, USA'),
(72, 40.694778, -73.985847, '100-120 Johnson Street, Brooklyn, NY 11201, USA'),
(73, 40.758896, -73.985130, 'Times Square, Manhattan, NY 10036, USA'),
(74, 42.358433, -71.059776, 'Boston, MA, USA'),
(75, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(76, 40.729118, -73.995506, 'New York University, 25 West 4th Street, New York, NY 10012, USA'),
(77, 40.694721, -73.985916, '49-59 Lawrence Street, Polytechnic Institute of New York University, Brooklyn, NY 11201, USA'),
(78, 40.694721, -73.985916, '49-59 Lawrence Street, Polytechnic Institute of New York University, Brooklyn, NY 11201, USA'),
(79, 42.358433, -71.059776, 'Boston, MA, USA'),
(80, 40.689922, -73.983810, 'AT&T'),
(81, 42.358433, -71.059776, 'Boston, MA, USA');

-- --------------------------------------------------------

--
-- Table structure for table `NOTE`
--

CREATE TABLE `NOTE` (
  `note_id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `words` text,
  `hyperlink` varchar(50) DEFAULT NULL,
  `location_id` int(11) DEFAULT NULL,
  `radius` int(5) DEFAULT NULL,
  `schedule_id` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`note_id`),
  KEY `NOTE_ibfk_1` (`uid`),
  KEY `NOTE_ibfk_2` (`location_id`),
  KEY `NOTE_ibfk_3` (`schedule_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=12 ;

--
-- Dumping data for table `NOTE`
--

INSERT INTO `NOTE` (`note_id`, `uid`, `words`, `hyperlink`, `location_id`, `radius`, `schedule_id`, `created_at`) VALUES
(3, 13, 'hello', '', 4, 500, 4, '2013-05-21 02:59:47'),
(4, 14, 'I am android.', '', 5, 500, 5, '2013-05-21 03:30:05'),
(5, 13, 'This is another testing post.', '', 6, 500, 6, '2013-05-22 15:59:13'),
(6, 14, 'This is a note from NYU, from 2013-05-22 16:35 to 2013-05-31 16:35, tag: me, food', '', 24, 500, 9, '2013-05-22 20:36:05'),
(7, 13, 'This is a note from Boston.', '', 40, 500, 11, '2013-05-22 22:57:50'),
(8, 14, 'This is NYU, tag: food', '', 64, 500, 15, '2013-05-23 18:29:35'),
(9, 14, 'poly', '', 67, 500, 16, '2013-05-23 18:39:48'),
(10, 16, 'New tag: study, location: Timesquare Every Tuesday', '', 73, 500, 18, '2013-05-23 21:01:51'),
(11, 13, 'New note.', '', 80, 500, 19, '2013-05-24 17:26:00');

-- --------------------------------------------------------

--
-- Table structure for table `PROFILE`
--

CREATE TABLE `PROFILE` (
  `profile_id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(20) DEFAULT NULL,
  `middle_name` varchar(20) DEFAULT NULL,
  `last_name` varchar(20) DEFAULT NULL,
  `gender` char(6) DEFAULT NULL,
  PRIMARY KEY (`profile_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `REPEAT`
--

CREATE TABLE `REPEAT` (
  `repeat_id` int(1) NOT NULL,
  `type` varchar(20) NOT NULL,
  PRIMARY KEY (`repeat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `REPEAT`
--

INSERT INTO `REPEAT` (`repeat_id`, `type`) VALUES
(0, 'Never'),
(1, 'Every day'),
(2, 'Every week');

-- --------------------------------------------------------

--
-- Table structure for table `RESPONSE_STATUS`
--

CREATE TABLE `RESPONSE_STATUS` (
  `rs_id` int(1) NOT NULL DEFAULT '0',
  `status` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`rs_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `RESPONSE_STATUS`
--

INSERT INTO `RESPONSE_STATUS` (`rs_id`, `status`) VALUES
(0, 'Pending'),
(1, 'Confirmed'),
(2, 'Rejected');

-- --------------------------------------------------------

--
-- Table structure for table `SCHEDULE`
--

CREATE TABLE `SCHEDULE` (
  `schedule_id` int(11) NOT NULL AUTO_INCREMENT,
  `starttime` datetime DEFAULT NULL,
  `endtime` datetime DEFAULT NULL,
  `repeat_id` int(1) DEFAULT '0',
  `dayofweek` int(11) DEFAULT NULL,
  PRIMARY KEY (`schedule_id`),
  KEY `starttime` (`starttime`),
  KEY `starttime_2` (`starttime`),
  KEY `repeat` (`repeat_id`),
  KEY `dayofweek` (`dayofweek`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=21 ;

--
-- Dumping data for table `SCHEDULE`
--

INSERT INTO `SCHEDULE` (`schedule_id`, `starttime`, `endtime`, `repeat_id`, `dayofweek`) VALUES
(4, '2013-05-22 00:00:00', '2013-05-22 00:00:00', 0, 0),
(5, '2013-05-20 11:28:00', '2013-05-20 11:43:00', 1, 0),
(6, '2013-05-22 11:59:00', '2013-05-31 11:59:00', 0, 0),
(7, '2013-05-22 14:57:00', '2013-05-31 14:57:00', 0, 0),
(8, '2013-05-22 10:00:00', '2013-05-22 15:00:00', 2, 3),
(9, '2013-05-22 16:35:00', '2013-05-31 16:35:00', 0, 0),
(10, '2013-05-22 18:55:00', '2013-05-31 18:55:00', 0, 0),
(11, '2013-05-22 18:57:00', '2013-05-31 18:57:00', 0, 0),
(12, '2013-05-22 19:12:00', '2013-05-31 19:12:00', 0, 0),
(13, '2013-05-22 19:14:00', '2013-05-31 19:14:00', 0, 0),
(14, '2013-05-23 14:27:00', '2013-05-31 14:27:00', 0, 0),
(15, '2013-05-23 14:29:00', '2013-05-31 14:29:00', 0, 0),
(16, '2013-05-23 12:00:00', '2013-05-23 13:00:00', 0, 0),
(17, '2013-05-23 12:00:00', '2013-05-23 13:00:00', 0, 0),
(18, '2013-05-23 00:00:00', '2013-05-23 23:59:00', 2, 1),
(19, '2013-05-24 13:25:00', '2013-05-24 17:25:00', 2, 0),
(20, '2013-05-24 13:27:00', '2013-05-31 13:27:00', 0, 0);

-- --------------------------------------------------------

--
-- Table structure for table `STATE`
--

CREATE TABLE `STATE` (
  `state_id` int(11) NOT NULL AUTO_INCREMENT,
  `state_name` varchar(20) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  PRIMARY KEY (`state_id`),
  KEY `STATE_ibfk_1` (`uid`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=11 ;

--
-- Dumping data for table `STATE`
--

INSERT INTO `STATE` (`state_id`, `state_name`, `uid`) VALUES
(1, 'kk', 13),
(2, 'at work', 13),
(3, 'just chilling', 13),
(4, 'new state', 13),
(5, 'lunch break', 13),
(6, 'just chilling', 14),
(7, 'new2', 13),
(8, 'at work', 14),
(9, 'at work', 16),
(10, 'new3', 13);

-- --------------------------------------------------------

--
-- Table structure for table `TAG`
--

CREATE TABLE `TAG` (
  `tag_id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`tag_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=10 ;

--
-- Dumping data for table `TAG`
--

INSERT INTO `TAG` (`tag_id`, `tag_name`) VALUES
(1, 'shopping'),
(2, 'food'),
(3, 'tourism'),
(4, 'transportation'),
(5, 'me'),
(6, 'new tag'),
(7, 'never'),
(8, 'study'),
(9, 'tag');

-- --------------------------------------------------------

--
-- Table structure for table `TAGS_IN_FILTER`
--

CREATE TABLE `TAGS_IN_FILTER` (
  `filter_id` int(11) NOT NULL DEFAULT '0',
  `tag_id` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`filter_id`,`tag_id`),
  KEY `TAGS_IN_FILTER_ibfk_2` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `TAGS_IN_FILTER`
--

INSERT INTO `TAGS_IN_FILTER` (`filter_id`, `tag_id`) VALUES
(2, 1),
(4, 1),
(8, 1),
(6, 2),
(7, 2),
(1, 5),
(3, 5),
(8, 5),
(2, 6),
(5, 7);

-- --------------------------------------------------------

--
-- Table structure for table `TAGS_IN_NOTE`
--

CREATE TABLE `TAGS_IN_NOTE` (
  `note_id` int(11) NOT NULL DEFAULT '0',
  `tag_id` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`note_id`,`tag_id`),
  KEY `tag_id` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `TAGS_IN_NOTE`
--

INSERT INTO `TAGS_IN_NOTE` (`note_id`, `tag_id`) VALUES
(3, 1),
(6, 1),
(7, 1),
(11, 1),
(7, 2),
(8, 2),
(9, 2),
(11, 2),
(7, 3),
(7, 4),
(4, 5),
(5, 5),
(6, 5),
(7, 5),
(9, 5),
(10, 8),
(11, 9);

-- --------------------------------------------------------

--
-- Table structure for table `USER`
--

CREATE TABLE `USER` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(20) DEFAULT NULL,
  `email` varchar(50) DEFAULT NULL,
  `password` varchar(60) DEFAULT NULL,
  `first_name` varchar(20) DEFAULT NULL,
  `last_name` varchar(20) DEFAULT NULL,
  `gender` char(6) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_location_id` int(11) DEFAULT NULL,
  `last_state_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`uid`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `location_id` (`last_location_id`),
  KEY `location_id_2` (`last_location_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=17 ;

--
-- Dumping data for table `USER`
--

INSERT INTO `USER` (`uid`, `username`, `email`, `password`, `first_name`, `last_name`, `gender`, `created_at`, `last_location_id`, `last_state_id`) VALUES
(13, 'apple', 'apple@apple.com', 'sha1$SA5BDpAz$92c4d90f2ab50437ce952d362fb6bc95e33c6da0', NULL, NULL, NULL, '2013-05-12 21:19:54', 81, 2),
(14, 'android', 'android@gmail.com', 'sha1$Q7k2WaD8$1bc6a5c815c6fc339ca34a37c0d15d3449eff5c0', NULL, NULL, NULL, '2013-05-21 03:29:26', 79, 6),
(15, 'nokia', 'nokia@gmail.com', 'sha1$0NpjMKMg$448dbc9fe208c4f4cdd0a5eadf4b232b7fae7b01', NULL, NULL, NULL, '2013-05-22 23:22:10', NULL, NULL),
(16, 'zx', 'zx@123.com', 'sha1$fSW1WGE7$74d49c71303683f00b8a713adeec7105b0f3b516', NULL, NULL, NULL, '2013-05-23 18:37:29', 75, 9);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `COMMENT`
--
ALTER TABLE `COMMENT`
  ADD CONSTRAINT `COMMENT_ibfk_1` FOREIGN KEY (`uid`) REFERENCES `USER` (`uid`),
  ADD CONSTRAINT `COMMENT_ibfk_2` FOREIGN KEY (`note_id`) REFERENCES `NOTE` (`note_id`);

--
-- Constraints for table `FILTER`
--
ALTER TABLE `FILTER`
  ADD CONSTRAINT `FILTER_ibfk_1` FOREIGN KEY (`state_id`) REFERENCES `STATE` (`state_id`),
  ADD CONSTRAINT `FILTER_ibfk_2` FOREIGN KEY (`location_id`) REFERENCES `LOCATION` (`location_id`),
  ADD CONSTRAINT `FILTER_ibfk_3` FOREIGN KEY (`schedule_id`) REFERENCES `SCHEDULE` (`schedule_id`);

--
-- Constraints for table `FRIENDSHIP`
--
ALTER TABLE `FRIENDSHIP`
  ADD CONSTRAINT `FRIENDSHIP_ibfk_1` FOREIGN KEY (`from_uid`) REFERENCES `USER` (`uid`),
  ADD CONSTRAINT `FRIENDSHIP_ibfk_2` FOREIGN KEY (`to_uid`) REFERENCES `USER` (`uid`),
  ADD CONSTRAINT `FRIENDSHIP_ibfk_3` FOREIGN KEY (`response_status`) REFERENCES `RESPONSE_STATUS` (`rs_id`);

--
-- Constraints for table `LIKE`
--
ALTER TABLE `LIKE`
  ADD CONSTRAINT `LIKE_ibfk_1` FOREIGN KEY (`note_id`) REFERENCES `NOTE` (`note_id`),
  ADD CONSTRAINT `LIKE_ibfk_2` FOREIGN KEY (`uid`) REFERENCES `USER` (`uid`);

--
-- Constraints for table `NOTE`
--
ALTER TABLE `NOTE`
  ADD CONSTRAINT `NOTE_ibfk_1` FOREIGN KEY (`uid`) REFERENCES `USER` (`uid`),
  ADD CONSTRAINT `NOTE_ibfk_2` FOREIGN KEY (`location_id`) REFERENCES `LOCATION` (`location_id`),
  ADD CONSTRAINT `NOTE_ibfk_3` FOREIGN KEY (`schedule_id`) REFERENCES `SCHEDULE` (`schedule_id`);

--
-- Constraints for table `SCHEDULE`
--
ALTER TABLE `SCHEDULE`
  ADD CONSTRAINT `SCHEDULE_ibfk_1` FOREIGN KEY (`repeat_id`) REFERENCES `REPEAT` (`repeat_id`),
  ADD CONSTRAINT `SCHEDULE_ibfk_2` FOREIGN KEY (`dayofweek`) REFERENCES `DAYOFWEEK` (`dow_id`);

--
-- Constraints for table `STATE`
--
ALTER TABLE `STATE`
  ADD CONSTRAINT `STATE_ibfk_1` FOREIGN KEY (`uid`) REFERENCES `USER` (`uid`);

--
-- Constraints for table `TAGS_IN_FILTER`
--
ALTER TABLE `TAGS_IN_FILTER`
  ADD CONSTRAINT `TAGS_IN_FILTER_ibfk_1` FOREIGN KEY (`filter_id`) REFERENCES `FILTER` (`filter_id`),
  ADD CONSTRAINT `TAGS_IN_FILTER_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `TAG` (`tag_id`);

--
-- Constraints for table `TAGS_IN_NOTE`
--
ALTER TABLE `TAGS_IN_NOTE`
  ADD CONSTRAINT `TAGS_IN_NOTE_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `TAG` (`tag_id`),
  ADD CONSTRAINT `TAGS_IN_NOTE_ibfk_4` FOREIGN KEY (`note_id`) REFERENCES `NOTE` (`note_id`) ON DELETE CASCADE;

--
-- Constraints for table `USER`
--
ALTER TABLE `USER`
  ADD CONSTRAINT `USER_ibfk_1` FOREIGN KEY (`last_location_id`) REFERENCES `LOCATION` (`location_id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
