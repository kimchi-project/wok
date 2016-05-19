<?xml version="1.0" encoding="UTF-8"?>
<!--
Project Wok
Copyright IBM Corp, 2016

Code derived from Project Kimchi
This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
-->
<xsl:stylesheet version="1.0"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        xmlns="http://www.w3.org/1999/xhtml">
    <xsl:output method="xml" indent="yes" encoding="UTF-8" />

    <xsl:template match="/">
        <html>
            <head>
                <title><xsl:value-of select="/cshelp/title" /></title>
                <meta charset="UTF-8" />
                <link rel="shortcut icon" href="../../images/logo.ico" />
                <link rel="stylesheet" type="text/css" href="../wok.css" />
            </head>
            <body>
                <xsl:apply-templates select="//cshelp" />
            </body>
        </html>
    </xsl:template>

    <xsl:template match="cshelp">
        <h1><xsl:value-of select="title" /></h1>
        <p class="shortdesc"><xsl:value-of select="shortdesc" /></p>
        <p class="csbody"><xsl:copy-of select="csbody/node()" /></p>
    </xsl:template>
</xsl:stylesheet>
