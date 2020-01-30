-- phpMyAdmin SQL Dump
-- version 4.9.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Jan 30, 2020 at 11:10 AM
-- Server version: 10.4.8-MariaDB
-- PHP Version: 7.3.11

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

-- --------------------------------------------------------

--
-- Table structure for table `RideDetails`
--

CREATE TABLE `RideDetails` (
  `RideID` int(11) NOT NULL,
  `CreatedBy` varchar(20) NOT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp(),
  `Source` varchar(20) NOT NULL,
  `Destination` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `RideDetails`
--

INSERT INTO `RideDetails` (`RideID`, `CreatedBy`, `TimeStamp`, `Source`, `Destination`) VALUES
(3, 'prams', '2020-01-12 17:42:12', 'mg road', 'banashankari');

-- --------------------------------------------------------

--
-- Table structure for table `RideUsers`
--

CREATE TABLE `RideUsers` (
  `RideID` int(11) NOT NULL,
  `username` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `UserDetails`
--

CREATE TABLE `UserDetails` (
  `username` varchar(20) NOT NULL,
  `password` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `UserDetails`
--

INSERT INTO `UserDetails` (`username`, `password`) VALUES
('eminem', 'musictobemurderedby'),
('prams', 'asdipvbawbvuiojadaos8fvhabwdnck');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `RideDetails`
--
ALTER TABLE `RideDetails`
  ADD PRIMARY KEY (`RideID`);

--
-- Indexes for table `RideUsers`
--
ALTER TABLE `RideUsers`
  ADD KEY `link_user` (`RideID`);

--
-- Indexes for table `UserDetails`
--
ALTER TABLE `UserDetails`
  ADD PRIMARY KEY (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `RideDetails`
--
ALTER TABLE `RideDetails`
  MODIFY `RideID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `RideUsers`
--
ALTER TABLE `RideUsers`
  ADD CONSTRAINT `link_user` FOREIGN KEY (`RideID`) REFERENCES `RideDetails` (`RideID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
