import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import type { Group, Mesh, MeshStandardMaterial } from 'three'

/**
 * The scene: a fly facing an approaching disk, with its brain lit by neural activity.
 *
 * Everything the viewer needs to understand the experiment is drawn in the scene rather than
 * described in text: the disk IS the stimulus, the fly faces it, and the brain glow IS the
 * measured descending-neuron response. No panel explains it because the scene does.
 *
 * Anatomy follows the real animal: large compound eyes on a small head, a thorax carrying both
 * wing pairs and all six legs, a banded tapering abdomen, and bristles. Proportions are
 * approximate — schematic for orientation, not a morphometric reconstruction.
 */

const THORAX = '#5c4a3a'
const ABDOMEN = '#7a6248'
const ABDOMEN_BAND = '#43372b'
const EYE = '#c0392b'
const EYE_DARK = '#5a1610'
const WING = '#e9eef2'
const VEIN = '#2c2622'
const LEG = '#2e2620'

/** Wing beat in Hz when nothing is measured. Idle animation, not a claim. */
const IDLE_HZ = 12

const OMMATIDIA = 240

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
      const length = Math.hypot(nx, ny, nz) || 1

      out.push({
        position: [(nx / length) * radius, (ny / length) * radius, (nz / length) * radius],
        rotation: [
          Math.atan2(Math.hypot(nx / length, ny / length), nz / length),
          Math.atan2(nx / length, nz / length),
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
  const facets = useOmmatidia(0.083)
  return (
    <group position={position} scale={scale}>
      <mesh>
        <sphereGeometry args={[0.086, 24, 18]} />
        <meshStandardMaterial color={EYE_DARK} roughness={0.42} metalness={0.05} />
      </mesh>
      {facets.map((f, i) => (
        <mesh key={i} position={f.position} rotation={f.rotation}>
          <cylinderGeometry args={[0.0092, 0.0092, 0.008, 6]} />
          <meshStandardMaterial
            color={EYE}
            roughness={0.3}
            metalness={0.12}
            emissive={EYE_DARK}
            emissiveIntensity={0.16}
          />
        </mesh>
      ))}
    </group>
  )
}

function WingVeins({ length, width }: { length: number; width: number }) {
  const veins: { from: [number, number, number]; to: [number, number, number] }[] = []
  for (const t of [-0.92, -0.52, -0.12, 0.28, 0.66]) {
    veins.push({
      from: [0, 0, -length * 0.48],
      to: [t * width * 0.5, 0, length * 0.5],
    })
  }
  for (const frac of [-0.1, 0.16, 0.4]) {
    const z = -length * 0.48 + length * frac
    veins.push({ from: [-width * 0.42, 0, z], to: [width * 0.34, 0, z + length * 0.05] })
  }
  veins.push({ from: [width * 0.16, 0, length * 0.2], to: [width * 0.3, 0, length * 0.31] })
  veins.push({ from: [width * 0.3, 0, length * 0.31], to: [width * 0.12, 0, length * 0.36] })
  veins.push({ from: [width * 0.12, 0, length * 0.36], to: [width * 0.02, 0, length * 0.3] })

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, length]} />
        <meshStandardMaterial
          color={WING}
          transparent
          opacity={0.26}
          side={2}
          roughness={0.14}
          metalness={0.04}
        />
      </mesh>
      {veins.map((v, i) => {
        // Vein endpoints are authored in (x, y, z) with y as the wing's span axis; the membrane
        // lies in the horizontal plane, so swap y and z into local coordinates here.
        const fx = v.from[0]
        const fy = v.from[2]
        const fz = v.from[1]
        const tx = v.to[0]
        const ty = v.to[2]
        const tz = v.to[1]
        const mx = (fx + tx) / 2
        const my = (fy + ty) / 2
        const mz = (fz + tz) / 2
        const dx = tx - fx
        const dy = ty - fy
        const dz = tz - fz
        const len = Math.hypot(dx, dy, dz)
        // Cylinders point along +Y by default; rotate +Y onto the vein direction.
        const ry = Math.atan2(Math.hypot(dx, dz), dy)
        const rz = Math.atan2(dx, dy)
        return (
          <mesh key={i} position={[mx, my, mz]} rotation={[0, ry, -rz]}>
            <cylinderGeometry args={[0.0016, 0.0016, len, 4]} />
            <meshStandardMaterial color={VEIN} roughness={0.7} />
          </mesh>
        )
      })}
    </group>
  )
}

function Leg({ z }: { z: number }) {
  return (
    <>
      <mesh position={[-0.06, -0.1, z]} rotation={[0.4, 0, 0.7]}>
        <cylinderGeometry args={[0.014, 0.013, 0.11, 6]} />
        <meshStandardMaterial color={LEG} roughness={0.85} />
      </mesh>
      <mesh position={[-0.14, -0.15, z + 0.01]} rotation={[0.1, 0, -0.55]}>
        <cylinderGeometry args={[0.026, 0.021, 0.15, 8]} />
        <meshStandardMaterial color={LEG} roughness={0.8} />
      </mesh>
      <mesh position={[-0.2, -0.24, z + 0.02]} rotation={[0.15, 0, -0.28]}>
        <cylinderGeometry args={[0.011, 0.008, 0.17, 6]} />
        <meshStandardMaterial color={LEG} roughness={0.85} />
      </mesh>
      {[0, 1, 2, 3, 4].map((seg) => (
        <mesh
          key={seg}
          position={[
            -0.235 - seg * 0.008,
            -0.325 - seg * 0.019,
            z + 0.02 + seg * 0.004,
          ]}
          rotation={[0.1, 0, -0.1]}
        >
          <cylinderGeometry args={[0.009 - seg * 0.001, 0.008 - seg * 0.001, 0.021, 5]} />
          <meshStandardMaterial color={LEG} roughness={0.88} />
        </mesh>
      ))}
      <mesh position={[-0.275, -0.425, z + 0.035]} rotation={[0.3, 0, -0.6]}>
        <coneGeometry args={[0.006, 0.02, 5]} />
        <meshStandardMaterial color={VEIN} roughness={0.9} />
      </mesh>
    </>
  )
}

interface SceneProps {
  /** Measured spike rate in Hz, or null when unmeasured. */
  spikeHz: number | null
  saturated: boolean
  /** True while the recorded stimulus plays. */
  playing: boolean
  /** 0..1 progress through the stimulus sequence; drives disk size and distance. */
  progress: number
}

export function FlyScene({ spikeHz, saturated, playing, progress }: SceneProps) {
  const leftWing = useRef<Group>(null)
  const rightWing = useRef<Group>(null)
  const brain = useRef<Mesh>(null)
  const disk = useRef<Mesh>(null)
  const bodyRef = useRef<Group>(null)

  const beatHz = spikeHz ?? IDLE_HZ

  useFrame((state, delta) => {
    const t = state.clock.elapsedTime
    const gate = playing ? 1 : 0.3
    const angle = Math.sin(t * beatHz * 2 * Math.PI) * 0.4 * gate

    if (leftWing.current) leftWing.current.rotation.z = angle
    if (rightWing.current) rightWing.current.rotation.z = -angle

    if (brain.current) {
      const material = brain.current.material as MeshStandardMaterial
      const pulse = 0.5 + 0.5 * Math.sin(t * 8)
      material.emissiveIntensity = spikeHz === null ? 0.15 : 0.5 + pulse * 0.7
      material.color.set(saturated ? '#991b1b' : '#38bdf8')
      material.emissive.set(saturated ? '#991b1b' : '#38bdf8')
    }

    // The disk approaches as the sequence progresses: it grows and moves toward the fly.
    // Parked it sits close enough to read as an object in the fly's field of view, and Start
    // drives it away and back so the approach is visible.
    if (disk.current) {
      const p = Math.max(0, Math.min(1, progress))
      const parked = p <= 0 && !playing
      // Parked: mid-distance and clearly visible, offset so it does not sit behind the fly.
      // Playing: starts far and small, arrives close and centred in the field of view.
      const distance = parked ? 0.95 : 1.5 - p * 1.05
      const scale = parked ? 0.4 : 0.2 + p * 0.6
      disk.current.scale.setScalar(scale)
      disk.current.position.set(parked ? 0.62 : 0, 0, distance)
    }

    // The fly holds position; a small idle bob keeps the scene alive when paused.
    if (bodyRef.current) {
      bodyRef.current.position.y = Math.sin(t * 1.6) * 0.012
      void delta
    }
  })

  return (
    <group>
      {/* The stimulus: an approaching dark disk, in the fly's field of view. */}
      <mesh ref={disk} position={[0, 0, 0.75]}>
        <circleGeometry args={[0.5, 48]} />
        <meshStandardMaterial
          color="#111827"
          emissive="#1e293b"
          emissiveIntensity={0.4}
          roughness={0.9}
        />
      </mesh>

      {/* The fly, side-on to the camera and facing the disk. A head-on fly hid the disk
          behind its own eyes; three-quarter view keeps the body, wings and the approaching
          object all readable at once. */}
      <group ref={bodyRef} rotation={[0.1, -2.35, 0.06]} scale={1.95}>
        <mesh position={[0, 0, 0.56]} scale={[1, 0.88, 0.9]}>
          <sphereGeometry args={[0.13, 24, 18]} />
          <meshStandardMaterial color={THORAX} roughness={0.75} />
        </mesh>

        <CompoundEye position={[-0.082, 0.038, 0.585]} scale={[0.82, 1, 0.95]} />
        <CompoundEye position={[0.082, 0.038, 0.585]} scale={[0.82, 1, 0.95]} />

        <mesh ref={brain} position={[0, -0.03, 0.55]}>
          <sphereGeometry args={[0.062, 20, 14]} />
          <meshStandardMaterial
            color="#38bdf8"
            emissive="#38bdf8"
            emissiveIntensity={0.15}
            roughness={0.5}
          />
        </mesh>

        <mesh position={[0, 0, 0.2]} scale={[1, 0.94, 1.05]}>
          <sphereGeometry args={[0.2, 28, 20]} />
          <meshStandardMaterial color={THORAX} roughness={0.72} />
        </mesh>

        {[
          { z: 0.0, r: 0.158 },
          { z: -0.15, r: 0.146 },
          { z: -0.285, r: 0.124 },
          { z: -0.395, r: 0.094 },
        ].map((seg, i) => (
          <mesh key={seg.z} position={[0, -0.008, seg.z]} scale={[1, 0.9, 1]}>
            <sphereGeometry args={[seg.r, 24, 18]} />
            <meshStandardMaterial
              color={i % 2 === 0 ? ABDOMEN : ABDOMEN_BAND}
              roughness={0.78}
            />
          </mesh>
        ))}

        <group ref={leftWing} position={[0.06, 0.13, 0.18]}>
          <group position={[-0.3, 0, -0.12]}>
            <WingVeins length={0.62} width={0.2} />
          </group>
          <group position={[-0.21, -0.012, -0.28]}>
            <WingVeins length={0.44} width={0.14} />
          </group>
        </group>

        <group ref={rightWing} position={[-0.06, 0.13, 0.18]}>
          <group position={[0.3, 0, -0.12]}>
            <WingVeins length={0.62} width={0.2} />
          </group>
          <group position={[0.21, -0.012, -0.28]}>
            <WingVeins length={0.44} width={0.14} />
          </group>
        </group>

        {[0.28, 0.17, 0.06].map((z) => (
          <group key={z}>
            <group scale={[-1, 1, 1]}>
              <Leg z={z} />
            </group>
            <Leg z={z} />
          </group>
        ))}

        {[-1, 1].map((side) => (
          <group key={side} position={[side * 0.05, 0.11, 0.66]}>
            <mesh rotation={[1.2, 0, side * 0.28]}>
              <cylinderGeometry args={[0.006, 0.0035, 0.2, 5]} />
              <meshStandardMaterial color={LEG} roughness={0.85} />
            </mesh>
            <mesh position={[side * 0.02, 0.08, 0.06]} rotation={[1.35, 0, side * 0.5]}>
              <cylinderGeometry args={[0.005, 0.002, 0.1, 5]} />
              <meshStandardMaterial color={LEG} roughness={0.85} />
            </mesh>
          </group>
        ))}
      </group>
    </group>
  )
}