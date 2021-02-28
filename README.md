# Coins-of-Ukraine
This repository is intended for those who collect Ukrainian coins. The repository contains functions and tools for parsing current prices and data on coins, analyzing the dynamics of growth in value, marking coins in a collection.

To get started, you need to run the "update_prices" function from the "parse" module with the required parameters. The launch will create a catalog with data on coins, images and history of value, and after the end of parsing, it will package the entire database into a relational form.

After the hierarchical and relational databases have been created, the following functions of the DBMS module are used to manipulate the copies and database formats:
+ pack_data () - packs a hierarchical directory into a relational view
+ pack_dynamics () - unpacks a relational copy into a hierarchical directory
+ unpack_data () - packs the hierarchically stored price change data into a relational view
+ unpack_dynamics () - unpacks a copy of price change data into a hierarchical view
