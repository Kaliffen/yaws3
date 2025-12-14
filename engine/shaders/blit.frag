#version 450 core
layout(location = 0) out vec4 outColor;

uniform sampler2D colorTex;

void main() {
    vec2 uv = gl_FragCoord.xy / textureSize(colorTex, 0);
    outColor = texture(colorTex, uv);
}
