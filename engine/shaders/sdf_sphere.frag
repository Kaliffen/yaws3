#version 450 core
layout(location = 0) out vec4 outColor;

uniform mat4 invViewProj;
uniform float sphereRadius;
uniform vec2 resolution;

float sdfSphere(vec3 p, float r) {
    return length(p) - r;
}

void main() {
    vec2 uv = (gl_FragCoord.xy / resolution) * 2.0 - 1.0;
    vec4 clip = vec4(uv, 1.0, 1.0);
    vec4 view = invViewProj * clip;
    vec3 rayDir = normalize(view.xyz / view.w);
    vec3 rayOrigin = vec3(0.0);

    float t = 0.0;
    vec3 p = rayOrigin;
    bool hit = false;
    for (int i = 0; i < 128; ++i) {
        p = rayOrigin + rayDir * t;
        float d = sdfSphere(p, sphereRadius);
        if (d < 0.001) {
            hit = true;
            break;
        }
        t += d;
        if (t > 1e6) break;
    }

    if (!hit) {
        outColor = vec4(0.0);
        return;
    }

    vec3 n = normalize(p);
    outColor = vec4(n * 0.5 + 0.5, 1.0);
}
