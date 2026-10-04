import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import type { Group, Mesh, MeshStandardMaterial } from 'three'

/**
 * Procedural Drosophila melanogaster, adult male.
 *
 * Built from primitives rather than a downloaded mesh. Three reasons:
 *   1. Licence. Every photoreal fruitfly asset online is CC-BY or CC-BY-NC with attribution
 *      terms that must be exactly right in a submission. Primitive geometry carries no
 *      third-party licence.
 *   2. Size. A textured scan mesh is 3-30 MB; this is a few KB and renders instantly with
 *      no network fetch on a judge's laptop.
 *   3. It is drivable. Wing beat frequency is bound to the measured spike rate, which a
 *      static mesh could not do without animation retargeting.
 *
 * Anatomy follows the real animal: large compound eyes on a small head, a thorax that is
 * the heaviest segment and carries both wing pairs and all six legs, a banded abdomen that
 * tapers to a point, and bristles. Proportions are approximate — this is a schematic for
 * orientation, not a morphometric reconstruction.
 */

// Body is a warm dark brown rather than black: under low-key lighting a near-black diffuse
// surface renders as a silhouette with no readable form.
const THORAX = '#5c4a3a'
const ABDOMEN = '#7a6248'
const ABDOMEN_BAND = '#43372b'
const EYE = '#c0392b'
const EYE_DARK = '#7b241c'
const WING = '#e8eef2'
const LEG = '#2e2620'

/** Wing beat in Hz when no measurement is available. Idle animation, not a claim. */
const IDLE_HZ = 12

interface FlyProps {
  /**
   * Measured spike rate in Hz, or null when unmeasured. Drives wing beat.
   * Per AGENTS.md §6 an unmeasured value must not render as a measured one, so the caller
   * passes null rather than 0.
   */
  spikeHz: number | null
  /** True when the readout is saturated at its refractory ceiling. */
  saturated: boolean
  running: boolean
}

export function Fly({ spikeHz, saturated, running }: FlyProps) {
  const leftWing = useRef<Group>(null)
  const rightWing = useRef<Group>(null)
  const brain = useRef<Mesh>(null)

  const beatHz = spikeHz ?? IDLE_HZ

  useFrame((state) => {
    const t = state.clock.elapsedTime

    // Wing beat. Amplitude eases in when running so the fly visibly starts.
    const gate = running ? 1 : 0.3
    const angle = Math.sin(t * beatHz * 2 * Math.PI) * 0.42 * gate

    if (leftWing.current) leftWing.current.rotation.z = angle
    if (rightWing.current) rightWing.current.rotation.z = -angle

    // Brain glow tracks the spike rate, and turns red when the readout is pinned.
    if (brain.current) {
      const material = brain.current.material as MeshStandardMaterial
      const pulse = 0.5 + 0.5 * Math.sin(t * 8)
      material.emissiveIntensity = spikeHz === null ? 0.15 : 0.5 + pulse * 0.7
      material.color.set(saturated ? '#991b1b' : '#38bdf8')
      material.emissive.set(saturated ? '#991b1b' : '#38bdf8')
    }
  })

  return (
    <group position={[0, 0, -0.02]} rotation={[0.1, -0.55, 0.08]} scale={1.05}>
      {/* Head. Small relative to the thorax, as in the animal. */}
      <mesh position={[0, 0, 0.56]} scale={[1, 0.88, 0.9]}>
        <sphereGeometry args={[0.13, 24, 18]} />
        <meshStandardMaterial color={THORAX} roughness={0.75} />
      </mesh>

      {/* Compound eyes. Large for the head size — that proportion is what makes a fly's
          head read as a fly's head — but they must not swallow the head entirely. */}
      {[-1, 1].map((side) => (
        <mesh
          key={side}
          position={[side * 0.082, 0.038, 0.585]}
          scale={[0.82, 1, 0.95]}
        >
          <sphereGeometry args={[0.088, 28, 20]} />
          <meshStandardMaterial
            color={EYE}
            roughness={0.22}
            metalness={0.05}
            emissive={EYE_DARK}
            emissiveIntensity={0.12}
          />
        </mesh>
      ))}

      {/* Brain, sitting between and below the eyes where it anatomically lies. */}
      <mesh ref={brain} position={[0, -0.03, 0.55]}>
        <sphereGeometry args={[0.062, 20, 14]} />
        <meshStandardMaterial
          color="#38bdf8"
          emissive="#38bdf8"
          emissiveIntensity={0.15}
          roughness={0.5}
        />
      </mesh>

      {/* Thorax: the wing-bearing segment and the heaviest part of the body. */}
      <mesh position={[0, 0, 0.2]} scale={[1, 0.94, 1.05]}>
        <sphereGeometry args={[0.2, 28, 20]} />
        <meshStandardMaterial color={THORAX} roughness={0.72} />
      </mesh>

      {/* Abdomen: four tapering segments with the dark banding real flies show. */}
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

      {/* Wings: two pairs per side, swept back over the abdomen as at rest.
          The pivot group sits on the hinge line so rotation.z raises and lowers the blade.
          Each blade is laid into the horizontal plane (-PI/2 about X) because planeGeometry
          is born in XY; without that they stand up like cards. */}
      <group ref={leftWing} position={[0.06, 0.13, 0.18]}>
        <mesh position={[-0.3, 0, -0.12]} rotation={[-Math.PI / 2, 0, 0.1]}>
          <planeGeometry args={[0.6, 0.19]} />
          <meshStandardMaterial
            color={WING}
            transparent
            opacity={0.32}
            side={2}
            roughness={0.12}
            metalness={0.04}
          />
        </mesh>
        <mesh position={[-0.21, -0.012, -0.28]} rotation={[-Math.PI / 2, 0, 0.14]}>
          <planeGeometry args={[0.42, 0.14]} />
          <meshStandardMaterial
            color={WING}
            transparent
            opacity={0.26}
            side={2}
            roughness={0.12}
            metalness={0.04}
          />
        </mesh>
      </group>

      <group ref={rightWing} position={[-0.06, 0.13, 0.18]}>
        <mesh position={[0.3, 0, -0.12]} rotation={[-Math.PI / 2, 0, -0.1]}>
          <planeGeometry args={[0.6, 0.19]} />
          <meshStandardMaterial
            color={WING}
            transparent
            opacity={0.32}
            side={2}
            roughness={0.12}
            metalness={0.04}
          />
        </mesh>
        <mesh position={[0.21, -0.012, -0.28]} rotation={[-Math.PI / 2, 0, -0.14]}>
          <planeGeometry args={[0.42, 0.14]} />
          <meshStandardMaterial
            color={WING}
            transparent
            opacity={0.26}
            side={2}
            roughness={0.12}
            metalness={0.04}
          />
        </mesh>
      </group>

      {/* Six legs, three per side, splayed from the thorax. */}
      {[
        { z: 0.28, angle: 1.0 },
        { z: 0.17, angle: 1.45 },
        { z: 0.06, angle: 1.8 },
      ].flatMap((leg) =>
        [1, -1].map((side) => (
          <group
            key={`${leg.z}-${side}`}
            position={[0, -0.12, leg.z]}
            rotation={[0.25, 0, side * leg.angle]}
          >
            {/* Femur */}
            <mesh position={[side * 0.11, -0.04, 0]} rotation={[0, 0, side * -0.75]}>
              <cylinderGeometry args={[0.012, 0.01, 0.2, 6]} />
              <meshStandardMaterial color={LEG} roughness={0.85} />
            </mesh>
            {/* Tibia, angled down */}
            <mesh position={[side * 0.2, -0.12, 0]} rotation={[0, 0, side * 0.35]}>
              <cylinderGeometry args={[0.008, 0.005, 0.19, 6]} />
              <meshStandardMaterial color={LEG} roughness={0.85} />
            </mesh>
          </group>
        )),
      )}

      {/* Antennae with a terminal flagellum. */}
      {[-1, 1].map((side) => (
        <mesh
          key={side}
          position={[side * 0.05, 0.11, 0.68]}
          rotation={[1.15, 0, side * 0.3]}
        >
          <cylinderGeometry args={[0.007, 0.003, 0.22, 5]} />
          <meshStandardMaterial color={LEG} roughness={0.85} />
        </mesh>
      ))}
    </group>
  )
}