import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { BufferGeometry, DoubleSide, Float32BufferAttribute, Group, MathUtils } from "three";
import type { DigitalTwinState, SimulationStartRequest } from "../state/types";

interface ThreeDesignViewProps {
  mission: SimulationStartRequest;
  state?: DigitalTwinState;
}

function createPlate(points: number[]) {
  const geometry = new BufferGeometry();
  geometry.setAttribute("position", new Float32BufferAttribute(points, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function WingPlate({ mirror = 1 }: { mirror?: 1 | -1 }) {
  const geometry = useMemo(
    () =>
      createPlate([
        -1.0,
        0.0,
        0.1 * mirror,
        0.35,
        0.0,
        2.1 * mirror,
        1.8,
        0.0,
        0.42 * mirror,
      ]),
    [mirror],
  );

  return (
    <mesh geometry={geometry} position={[0.06, 0, 0]}>
      <meshStandardMaterial color="#313629" roughness={0.82} metalness={0.28} side={DoubleSide} />
    </mesh>
  );
}

function TailFin({ z, tilt }: { z: number; tilt: number }) {
  return (
    <group position={[1.72, 0.18, z]} rotation={[0.25, 0, tilt]}>
      <mesh>
        <boxGeometry args={[0.82, 0.12, 0.5]} />
        <meshStandardMaterial color="#0b0b09" roughness={0.7} metalness={0.35} />
      </mesh>
      <mesh position={[-0.08, 0.08, 0]}>
        <boxGeometry args={[0.78, 0.06, 0.12]} />
        <meshStandardMaterial color="#9f5f2b" emissive="#4a1c04" emissiveIntensity={0.1} roughness={0.55} />
      </mesh>
    </group>
  );
}

function EngineSpine({ coolingPower }: { coolingPower: number }) {
  return (
    <group position={[0.46, -0.18, 0]}>
      <mesh rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.075, 0.075, 3.3, 18]} />
        <meshStandardMaterial color="#15191a" metalness={0.9} roughness={0.25} />
      </mesh>

      {[-0.62, 0.03, 0.68].map((x) => (
        <mesh key={x} position={[x, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.16, 0.16, 0.34, 18]} />
          <meshStandardMaterial color="#4f574f" metalness={0.55} roughness={0.42} />
        </mesh>
      ))}

      {[-0.28, 0.38, 0.98].map((x) => (
        <mesh key={x} position={[x, 0.01, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.03, 0.03, 0.42, 12]} />
          <meshStandardMaterial color="#8bb4c4" emissive="#5edff5" emissiveIntensity={coolingPower * 0.55} metalness={0.7} roughness={0.22} />
        </mesh>
      ))}

      <mesh position={[1.92, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.26, 0.16, 0.52, 24]} />
        <meshStandardMaterial color="#f1eab2" emissive="#f3e278" emissiveIntensity={0.25 + coolingPower * 0.35} metalness={0.75} roughness={0.25} />
      </mesh>
      <pointLight position={[2.2, 0, 0]} color="#fff0a0" intensity={1.2 + coolingPower * 1.8} distance={4.5} />
    </group>
  );
}

function WaveriderVehicle({ mission, state }: ThreeDesignViewProps) {
  const groupRef = useRef<Group>(null);
  const mach = state?.aircraft.mach ?? mission.initial_conditions.mach;
  const surfaceTemp = state?.thermal.max_surface_temp_k ?? 900;
  const heat = MathUtils.clamp((surfaceTemp - 450) / 1700, 0, 1);
  const coolingPower = MathUtils.clamp(mission.cooling.mass_flow_kg_s / 2, 0, 1);
  const spanScale = MathUtils.clamp(mission.vehicle.reference_area_m2 / 22, 0.72, 1.42);

  useFrame(({ clock, pointer }) => {
    if (!groupRef.current) return;
    const t = clock.getElapsedTime();
    groupRef.current.rotation.y = -0.56 + Math.sin(t * 0.22) * 0.08 + pointer.x * 0.22;
    groupRef.current.rotation.x = 0.42 + Math.sin(t * 0.31) * 0.035 - pointer.y * 0.1;
    groupRef.current.rotation.z = -0.34 + Math.sin(t * 0.18) * 0.04;
    groupRef.current.position.y = Math.sin(t * 0.7) * 0.055;
  });

  return (
    <group ref={groupRef} scale={[1.14, 1.14, spanScale]}>
      <mesh position={[-1.8, 0.01, 0]} rotation={[0, 0, Math.PI / 2]}>
        <coneGeometry args={[0.27, 1.15, 7]} />
        <meshStandardMaterial color="#c34910" emissive="#e65912" emissiveIntensity={0.15 + heat * 0.65} roughness={0.65} metalness={0.25} />
      </mesh>

      <mesh position={[-0.42, 0.02, 0]} rotation={[0, 0, 0.03]}>
        <boxGeometry args={[2.28, 0.34, 0.54]} />
        <meshStandardMaterial color="#222920" roughness={0.78} metalness={0.34} />
      </mesh>

      <mesh position={[0.3, 0.14, 0]}>
        <boxGeometry args={[2.36, 0.16, 0.92]} />
        <meshStandardMaterial color="#2d3428" roughness={0.86} metalness={0.22} />
      </mesh>

      <WingPlate mirror={1} />
      <WingPlate mirror={-1} />

      <mesh position={[0.45, -0.16, 0]}>
        <boxGeometry args={[1.8, 0.12, 1.15]} />
        <meshStandardMaterial color="#25291f" roughness={0.9} metalness={0.16} side={DoubleSide} />
      </mesh>

      <EngineSpine coolingPower={coolingPower} />
      <TailFin z={0.62} tilt={0.26} />
      <TailFin z={-0.62} tilt={-0.26} />

      <mesh position={[2.47, -0.18, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.42, 0.32, 0.54, 4]} />
        <meshStandardMaterial color="#050504" roughness={0.68} metalness={0.45} />
      </mesh>

      <mesh position={[0.04, 0.38, 0.03]}>
        <boxGeometry args={[0.7, 0.08, 0.9]} />
        <meshStandardMaterial color="#111611" transparent opacity={0.45} roughness={0.35} metalness={0.2} />
      </mesh>

      <pointLight position={[-2.25, 0.15, 0]} color="#ff5e13" intensity={0.9 + heat * 2.2} distance={3.2} />
      <pointLight position={[-0.4, 1.5, 2.2]} color="#63f5cf" intensity={0.55 + mach * 0.04} distance={5} />
    </group>
  );
}

function ShockSheets({ mach }: { mach: number }) {
  const opacity = MathUtils.clamp((mach - 4) / 7, 0.12, 0.42);
  return (
    <group rotation={[0.45, -0.54, -0.34]}>
      {[0, 1, 2].map((index) => (
        <mesh key={index} position={[-1.25 + index * 0.42, -0.1, 0]} rotation={[0, 0, -0.18]}>
          <planeGeometry args={[2.6 + index * 0.3, 0.78 + index * 0.18]} />
          <meshBasicMaterial color="#6ef2d3" transparent opacity={opacity * (0.28 - index * 0.055)} side={DoubleSide} depthWrite={false} />
        </mesh>
      ))}
    </group>
  );
}

export function ThreeDesignView({ mission, state }: ThreeDesignViewProps) {
  const mach = state?.aircraft.mach ?? mission.initial_conditions.mach;
  const surfaceTemp = state?.thermal.max_surface_temp_k ?? 900;
  const heatFlux = state?.thermal.heat_flux_w_m2 ?? 0;
  const tpsLabel = mission.tps.material_id.replaceAll("_", " ").toUpperCase();

  return (
    <section className="design-shell">
      <Canvas camera={{ position: [5.6, 3.2, 6.7], fov: 38 }} dpr={[1, 1.75]} gl={{ antialias: true }}>
        <color attach="background" args={["#11130f"]} />
        <fog attach="fog" args={["#11130f", 6, 14]} />
        <ambientLight intensity={0.24} />
        <directionalLight position={[3.5, 5.2, 2.4]} intensity={1.05} color="#fff1cb" />
        <directionalLight position={[-4, 2.1, -3.8]} intensity={0.36} color="#63ffd5" />
        <ShockSheets mach={mach} />
        <WaveriderVehicle mission={mission} state={state} />
      </Canvas>

      <div className="design-hud design-hud-left">
        <p>REGEN-TWIN V1 + WAVERIDER CLASS</p>
        <span>MACH {mach.toFixed(2)}</span>
        <span>TPS TEMP {Math.round(surfaceTemp)} K</span>
        <span>HEAT FLUX {(heatFlux / 1_000_000).toFixed(2)} MW/m2</span>
      </div>

      <div className="design-hud design-hud-right">
        <span>TPS: {tpsLabel} - LAMINAR LEADING EDGES</span>
        <span>SCRAMJET CORE - REGEN INTERFACE</span>
        <span>DESIGN: HYPER ADVANCED CONCEPT</span>
      </div>
    </section>
  );
}
