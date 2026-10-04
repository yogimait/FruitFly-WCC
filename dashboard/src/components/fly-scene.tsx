import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import type { Group, Mesh, MeshStandardMaterial } from 'three'

/**
 * Procedural Drosophila melanogaster, adult male — elongated build.
 *
 * Built from primitives rather than a downloaded mesh. Three reasons:
 *   1. Licence. Every photoreal fruitfly asset found online is CC-BY or CC-BY-NC with attribution
 *      terms that must be exactly right in a submission.
 *   2. Size. A textured scan is 3-30 MB; this is a few KB and renders with no network fetch.
 *   3. It is drivable. Wing beat frequency is bound to the measured spike rate.
 *
 * Silhouette follows the real animal: a small head, a heavy thorax, and a long abdomen that
 * tapers through five visibly banded segments — roughly 1.4x the combined head+thorax length,
 * which is what makes a fly read as a fly rather than as a generic insect. Legs are long and
 * spindly, wings are held swept back, compound eyes are large and red.
 */

const HEAD = '#6b5340'
const THORAX = '#7a5c42'
const ABDOMEN_A = '#8a6a4c'
const ABDOMEN_B = '#5d4632'
const ABDOMEN_C = '#3a2c20'
const EYE = '#c0392b'
const EYE_DARK = '#5a1610'
const WING = '#dbe6ec'
const VEIN = '#3a2f26'
const LEG = '#3b2f26'
const BRISTLE = '#1a1512'

const IDLE_HZ = 12
const OMMATIDIA = 260

/** Evenly distributed hexagonal facets over a forward-facing hemisphere. */
function useOmmatidia(radius: number) {
  return (() => {
    const golden = Math.PI * (3 - Math.sqrt(5))
    const out: {
      position: [number, number, number]
      rotation: [number, number, number]
    }[] = []
    for (let i = 0; i < OMMATIDIA; i++) {
      const y = 1 - (i / (OMMATIDIA - 1)) * 2
      const r = Math.sqrt(Math.max(0, 1 - y * y))
      const theta = golden * i
      const nx = Math.cos(theta) * r
      const nz = r * 0.55 + 0.45
      const ny = y
      if (nz < 0.42) continue
      const len = Math.hypot(nx, ny, nz) || 1
      const px = (nx / len) * radius
      const py = (ny / len) * radius
      const pz = (nz / len) * radius
      out.push({
        position: [px, py, pz],
        rotation: [
          Math.atan2(Math.hypot(px, py), pz),
          Math.atan2(px, pz),
          0,
        ],
      })
    }
    return out
  })()
}

function CompoundEye({
  position,
  scale,
}: {
  position: [number, number, number]
  scale: [number, number, number]
}) {
  const facets = useOmmatidia(0.082)
  return (
    <group position={position} scale={scale}>
      <mesh>
        <sphereGeometry args={[0.085, 24, 18]} />
        <meshStandardMaterial color={EYE_DARK} roughness={0.4} metalness={0.06} />
      </mesh>
      {facets.map((f, i) => (
        <mesh key={i} position={f.position} rotation={f.rotation}>
          <cylinderGeometry args={[0.0088, 0.0088, 0.008, 6]} />
          <meshStandardMaterial
            color={EYE}
            roughness={0.28}
            metalness={0.14}
            emissive={EYE_DARK}
            emissiveIntensity={0.18}
          />
        </mesh>
      ))}
    </group>
  )
}

/** One wing: membrane plus longitudinal veins, cross-veins and two closed cells. */
function Wing({ length, width }: { length: number; width: number }) {
  const veins = useRef<THREE.Mesh[]>([])

  const segments = (() => {
    const out: { from: THREE.Vector3; to: THREE.Vector3 }[] = []
    for (const t of [-0.9, -0.5, -0.1, 0.3, 0.68]) {
      out.push({
        from: new THREE.Vector3(0, 0, -length * 0.48),
        to: new THREE.Vector3(t * width * 0.5, 0, length * 0.5),
      })
    }
    for (const frac of [-0.08, 0.18, 0.42]) {
      const z = -length * 0.48 + length * frac
      out.push({
        from: new THREE.Vector3(-width * 0.42, 0, z),
        to: new THREE.Vector3(width * 0.34, 0, z + length * 0.05),
      })
    }
    out.push({
      from: new THREE.Vector3(width * 0.16, 0, length * 0.2),
      to: new THREE.Vector3(width * 0.3, 0, length * 0.31),
    })
    out.push({
      from: new THREE.Vector3(width * 0.3, 0, length * 0.31),
      to: new THREE.Vector3(width * 0.12, 0, length * 0.37),
    })
    out.push({
      from: new THREE.Vector3(width * 0.12, 0, length * 0.37),
      to: new THREE.Vector3(width * 0.02, 0, length * 0.3),
    })
    return out
  })()

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, length]} />
        <meshStandardMaterial
          color={WING}
          transparent
          opacity={0.3}
          side={THREE.DoubleSide}
          roughness={0.12}
          metalness={0.05}
        />
      </mesh>
      {segments.map((s, i) => {
        const mid = s.from.clone().add(s.to).multiplyScalar(0.5)
        const dir = s.to.clone().sub(s.from)
        const len = dir.length()
        const quat = new THREE.Quaternion().setFromUnitVectors(
          new THREE.Vector3(0, 1, 0),
          dir.clone().normalize(),
        )
        const euler = new THREE.Euler().setFromQuaternion(quat)
        return (
          <mesh
            key={i}
            ref={(el) => {
              if (el) veins.current[i] = el
            }}
            position={mid}
            rotation={[euler.x, euler.y, euler.z]}
          >
            <cylinderGeometry args={[0.0014, 0.0014, len, 4]} />
            <meshStandardMaterial color={VEIN} roughness={0.7} />
          </mesh>
        )
      })}
    </group>
  )
}

/** One leg: coxa, thick femur, long thin tibia, five-segment tarsus, claws. */
function Leg({ z, splay }: { z: number; splay: number }) {
  return (
    <group position={[0, -0.1, z]}>
      <mesh position={[-0.07 * splay, -0.06, 0]} rotation={[0.5, 0, 0.8 * splay]}>
        <cylinderGeometry args={[0.012, 0.011, 0.12, 6]} />
        <meshStandardMaterial color={LEG} roughness={0.85} />
      </mesh>
      <mesh position={[-0.17 * splay, -0.17, 0.01]} rotation={[0.1, 0, -0.5]}>
        <cylinderGeometry args={[0.022, 0.017, 0.24, 8]} />
        <meshStandardMaterial color={LEG} roughness={0.8} />
      </mesh>
      <mesh position={[-0.28 * splay, -0.35, 0.02]} rotation={[0.15, 0, -0.22]}>
        <cylinderGeometry args={[0.009, 0.006, 0.3, 6]} />
        <meshStandardMaterial color={LEG} roughness={0.85} />
      </mesh>
      {[0, 1, 2, 3, 4].map((seg) => (
        <mesh
          key={seg}
          position={[
            -0.31 * splay - seg * 0.006,
            -0.5 - seg * 0.024,
            0.02 + seg * 0.005,
          ]}
          rotation={[0.1, 0, -0.08]}
        >
          <cylinderGeometry
            args={[0.008 - seg * 0.0009, 0.007 - seg * 0.0009, 0.026, 5]}
          />
          <meshStandardMaterial color={LEG} roughness={0.88} />
        </mesh>
      ))}
      <mesh position={[-0.34 * splay, -0.63, 0.04]} rotation={[0.3, 0, -0.55]}>
        <coneGeometry args={[0.005, 0.018, 5]} />
        <meshStandardMaterial color={VEIN} roughness={0.9} />
      </mesh>
    </group>
  )
}

interface SceneProps {
  spikeHz: number | null
  saturated: boolean
  playing: boolean
  progress: number
  /** Live camera motion energy 0..1, or null when using the synthetic stimulus. */
  liveMotion: number | null
  /** Live DNp01 output rate from the camera-driven encoder, 0..1. Null when synthetic. */
  liveDrive: number | null
}

export function FlyScene({
  spikeHz,
  saturated,
  playing,
  progress,
  liveMotion,
  liveDrive,
}: SceneProps) {
  const leftWing = useRef<Group>(null)
  const rightWing = useRef<Group>(null)
  const brain = useRef<Mesh>(null)
  const disk = useRef<Mesh>(null)
  const body = useRef<Group>(null)
  const wings = useRef<Group>(null)

  const beatHz = spikeHz ?? IDLE_HZ
  const usingCamera = liveMotion !== null

  useFrame((state) => {
    const t = state.clock.elapsedTime

    // In camera mode the fly is driven by the LIVE motion energy from the viewer's own
    // frames, so moving something in front of the camera visibly moves the fly. This is a
    // visualisation of the stimulus reaching the encoder — NOT a neural measurement. The
    // recorded spike counts elsewhere on the page are not recomputed here, and the UI says so.
    // In synthetic mode the recorded spike rate drives the wings instead.
    const motion = liveMotion ?? 0
    const active = usingCamera || playing
    const gate = active ? 1 : 0.3

    // Beat and amplitude both scale with the stimulus, from the normalised value which already
    // carries a visible baseline. At rest the fly idles at ~24 Hz; a moving subject pushes it
    // toward ~180 Hz with a much larger stroke, so the change is obvious.
    const effectiveHz = usingCamera
      ? IDLE_HZ + motion * 170
      : beatHz
    const stroke = usingCamera ? 0.18 + motion * 0.42 : 0.42
    const angle = Math.sin(t * effectiveHz * 2 * Math.PI) * stroke * gate

    if (leftWing.current) leftWing.current.rotation.z = angle
    if (rightWing.current) rightWing.current.rotation.z = -angle

    if (brain.current) {
      const m = brain.current.material as MeshStandardMaterial
      if (usingCamera) {
        // Brightness tracks the live descending-neuron output count, so the fly's visible
        // response and the raster below it are driven by the same number. Falls back to the
        // motion level when the encoder has not produced output yet.
        const drive = liveDrive ?? motion
        m.emissiveIntensity = 0.2 + drive * 4.5
      } else if (spikeHz === null) {
        m.emissiveIntensity = 0.15
      } else {
        const pulse = 0.5 + 0.5 * Math.sin(t * 8)
        m.emissiveIntensity = 0.5 + pulse * 0.7
      }
      const colour = saturated && !usingCamera ? '#991b1b' : '#38bdf8'
      m.color.set(colour)
      m.emissive.set(colour)
    }

    if (disk.current) {
      if (usingCamera) {
        // Camera mode: the disk is hidden, because the real scene IS the stimulus.
        disk.current.visible = false
      } else {
        disk.current.visible = true
        const p = Math.max(0, Math.min(1, progress))
        const parked = p <= 0 && !playing
        // Held clear of the body AND on the side the fly is facing, so it reads as an object
        // in front of the fly rather than behind it or attached to it. Parked is far and
        // offset; playing approaches to sit directly ahead.
        const distance = parked ? 1.0 : 1.5 - p * 0.7
        const scale = parked ? 0.26 : 0.18 + p * 0.34
        disk.current.scale.setScalar(scale)
        disk.current.position.set(parked ? 1.35 : 1.0, 0.02, distance)
      }
    }

    if (body.current) {
      // Idle bob, plus a forward lean under stimulus so the body itself visibly responds.
      body.current.position.y = Math.sin(t * 1.5) * 0.01
      const lean = usingCamera ? motion * 0.22 : playing ? 0.08 : 0
      body.current.rotation.x = 0.08 - lean + Math.sin(t * 2.2) * 0.01
    }

    // A whole-body twitch with the same drive as the wings, so the animal reads as alive.
    if (wings.current) {
      wings.current.rotation.z = Math.sin(t * effectiveHz * Math.PI) * 0.03 * gate
    }
  })

  // Five banded abdominal segments, tapering — the long body that makes it read as a fly.
  const abdomen = [
    { z: -0.06, r: 0.155, c: ABDOMEN_A },
    { z: -0.28, r: 0.146, c: ABDOMEN_B },
    { z: -0.47, r: 0.126, c: ABDOMEN_A },
    { z: -0.63, r: 0.102, c: ABDOMEN_C },
    { z: -0.76, r: 0.072, c: ABDOMEN_B },
  ]

  const bristlePositions: { p: [number, number, number]; r: [number, number, number] }[] = []
  for (let i = 0; i < 34; i++) {
    const t = i / 33
    const z = 0.32 - t * 1.0
    const side = i % 2 === 0 ? 1 : -1
    const tilt = 0.85 + ((i * 2.399) % 1) * 0.55
    bristlePositions.push({
      p: [side * 0.08, 0.11 + (i % 3) * 0.022, z],
      r: [0, 0, side * tilt],
    })
  }

  return (
    <group>
      {/* The stimulus: an approaching dark disk, ahead of the fly's head. */}
      <mesh ref={disk} position={[1.35, 0.02, 1.0]}>
        <circleGeometry args={[0.5, 48]} />
        <meshStandardMaterial
          color="#0f172a"
          emissive="#334155"
          emissiveIntensity={0.55}
          roughness={0.9}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* The fly, turned so its head faces the stimulus disk at +X. */}
      <group ref={body} rotation={[0.08, 2.42, 0.05]} scale={2.15}>
        {/* Head */}
        <mesh position={[0, 0.01, 0.6]} scale={[0.92, 0.9, 0.95]}>
          <sphereGeometry args={[0.115, 24, 18]} />
          <meshStandardMaterial color={HEAD} roughness={0.75} />
        </mesh>

        {/* Compound eyes */}
        <CompoundEye position={[-0.072, 0.035, 0.63]} scale={[0.78, 1, 0.95]} />
        <CompoundEye position={[0.072, 0.035, 0.63]} scale={[0.78, 1, 0.95]} />

        {/* Brain, between and below the eyes where it anatomically lies. */}
        <mesh ref={brain} position={[0, -0.028, 0.59]}>
          <sphereGeometry args={[0.055, 20, 14]} />
          <meshStandardMaterial
            color="#38bdf8"
            emissive="#38bdf8"
            emissiveIntensity={0.15}
            roughness={0.5}
          />
        </mesh>

        {/* Thorax: heavy, wing-bearing, the biggest single segment. */}
        <mesh position={[0, 0, 0.22]} scale={[0.98, 0.92, 1.08]}>
          <sphereGeometry args={[0.185, 28, 20]} />
          <meshStandardMaterial color={THORAX} roughness={0.72} />
        </mesh>

        {/* Long banded abdomen */}
        {abdomen.map((seg) => (
          <mesh key={seg.z} position={[0, -0.012, seg.z]} scale={[1, 0.88, 1.12]}>
            <sphereGeometry args={[seg.r, 24, 18]} />
            <meshStandardMaterial color={seg.c} roughness={0.76} />
          </mesh>
        ))}

        {/* Wings: two pairs, swept back over the abdomen. */}
        <group ref={wings}>
          <group ref={leftWing} position={[0.055, 0.125, 0.2]}>
            <group position={[-0.32, 0, -0.16]}>
              <Wing length={0.72} width={0.22} />
            </group>
            <group position={[-0.24, -0.014, -0.34]}>
              <Wing length={0.5} width={0.15} />
            </group>
          </group>

          <group ref={rightWing} position={[-0.055, 0.125, 0.2]}>
            <group position={[0.32, 0, -0.16]}>
              <Wing length={0.72} width={0.22} />
            </group>
            <group position={[0.24, -0.014, -0.34]}>
              <Wing length={0.5} width={0.15} />
            </group>
          </group>
        </group>

        {/* Six long legs, three per side */}
          {[0.3, 0.19, 0.08].map((z) => (
            <group key={z}>
              <group scale={[-1, 1, 1]}>
                <Leg z={z} splay={1} />
              </group>
              <Leg z={z} splay={1} />
            </group>
          ))}

        {/* Bristles along thorax and abdomen */}
        {bristlePositions.map((b, i) => (
          <mesh key={i} position={b.p} rotation={b.r}>
            <cylinderGeometry args={[0.0016, 0.0007, 0.07, 3]} />
            <meshStandardMaterial color={BRISTLE} roughness={0.95} />
          </mesh>
        ))}

        {/* Antennae with flagella */}
        {[-1, 1].map((side) => (
          <group key={side} position={[side * 0.045, 0.1, 0.69]}>
            <mesh rotation={[1.25, 0, side * 0.26]}>
              <cylinderGeometry args={[0.0055, 0.0032, 0.2, 5]} />
              <meshStandardMaterial color={LEG} roughness={0.85} />
            </mesh>
            <mesh position={[side * 0.022, 0.085, 0.06]} rotation={[1.4, 0, side * 0.5]}>
              <cylinderGeometry args={[0.0045, 0.0018, 0.1, 5]} />
              <meshStandardMaterial color={LEG} roughness={0.85} />
            </mesh>
          </group>
        ))}
      </group>
    </group>
  )
}