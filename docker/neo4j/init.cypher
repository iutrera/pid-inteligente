// P&ID Inteligente — Neo4j Initial Schema
// This file runs on container first start to create constraints and indexes.

// =========================================================================
// Uniqueness constraints
// =========================================================================

CREATE CONSTRAINT pid_tag_unique IF NOT EXISTS
FOR (e:Equipment) REQUIRE (e.pid_id, e.tag_number) IS UNIQUE;

CREATE CONSTRAINT instrument_tag_unique IF NOT EXISTS
FOR (i:Instrument) REQUIRE (i.pid_id, i.tag_number) IS UNIQUE;

CREATE CONSTRAINT line_number_unique IF NOT EXISTS
FOR (l:PipingSegment) REQUIRE (l.pid_id, l.line_number) IS UNIQUE;

CREATE CONSTRAINT nozzle_id_unique IF NOT EXISTS
FOR (n:Nozzle) REQUIRE (n.pid_id, n.id) IS UNIQUE;

CREATE CONSTRAINT valve_tag_unique IF NOT EXISTS
FOR (v:Valve) REQUIRE (v.pid_id, v.tag_number) IS UNIQUE;

// =========================================================================
// Indexes: speed up common queries
// =========================================================================

CREATE INDEX equipment_type IF NOT EXISTS FOR (e:Equipment) ON (e.dexpi_class);
CREATE INDEX instrument_type IF NOT EXISTS FOR (i:Instrument) ON (i.dexpi_class);
CREATE INDEX node_pid IF NOT EXISTS FOR (n:PidNode) ON (n.pid_id);
CREATE INDEX node_tag IF NOT EXISTS FOR (n:PidNode) ON (n.tag_number);
CREATE INDEX node_type IF NOT EXISTS FOR (n:PidNode) ON (n.node_type);
CREATE INDEX piping_fluid IF NOT EXISTS FOR (p:PipingSegment) ON (p.fluid_code);
CREATE INDEX utility_fluid IF NOT EXISTS FOR (u:UtilityLine) ON (u.fluid_code);
