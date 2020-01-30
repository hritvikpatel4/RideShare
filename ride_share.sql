-- phpMyAdmin SQL Dump
-- version 5.0.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 30, 2020 at 02:14 AM
-- Server version: 10.4.11-MariaDB
-- PHP Version: 7.4.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `ride_share`
--
CREATE DATABASE IF NOT EXISTS `ride_share` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `ride_share`;

-- --------------------------------------------------------

--
-- Table structure for table `ridedetails`
--

CREATE TABLE `ridedetails` (
  `rideid` int(11) NOT NULL,
  `created_by` varchar(255) NOT NULL,
  `timestamp` text NOT NULL,
  `source` varchar(1000) NOT NULL,
  `destination` varchar(1000) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `rideusers`
--

CREATE TABLE `rideusers` (
  `rideid` int(11) NOT NULL,
  `username` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `userdetails`
--

CREATE TABLE `userdetails` (
  `username` varchar(500) NOT NULL,
  `password` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ridedetails`
--
ALTER TABLE `ridedetails`
  ADD PRIMARY KEY (`rideid`),
  ADD KEY `del_user2` (`created_by`);

--
-- Indexes for table `rideusers`
--
ALTER TABLE `rideusers`
  ADD KEY `link_user` (`rideid`),
  ADD KEY `del_user` (`username`);

--
-- Indexes for table `userdetails`
--
ALTER TABLE `userdetails`
  ADD PRIMARY KEY (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `ridedetails`
--
ALTER TABLE `ridedetails`
  MODIFY `rideid` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `ridedetails`
--
ALTER TABLE `ridedetails`
  ADD CONSTRAINT `del_user2` FOREIGN KEY (`created_by`) REFERENCES `userdetails` (`username`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `rideusers`
--
ALTER TABLE `rideusers`
  ADD CONSTRAINT `del_user` FOREIGN KEY (`username`) REFERENCES `userdetails` (`username`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `link_user` FOREIGN KEY (`rideid`) REFERENCES `ridedetails` (`rideid`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
