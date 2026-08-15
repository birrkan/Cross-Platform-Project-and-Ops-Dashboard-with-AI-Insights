-- Grants the xwiki user privileges to create subwikis.
-- Taken from the official XWiki docker repo (17/mariadb-tomcat/mariadb/init.sql).
-- Reference: https://github.com/xwiki/xwiki-docker/blob/master/17/mariadb-tomcat/mariadb/init.sql
grant all privileges on *.* to xwiki@'%'
