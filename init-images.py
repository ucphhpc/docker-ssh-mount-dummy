import argparse
import os
import yaml
from jinja2 import Template
from utils.io import load, write, copy

current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(current_dir)

PACKAGE_NAME = "generate-gocd-config"
REPO_NAME = "docker-ssh-mount-dummy"
ENVIRONMENT = "bare_metal_docker_image"
GROUP = "bare_metal_docker_image"
TEAMPLATE = "bare_metal_docker_image"
COMMIT_TAG = "GO_REVISION_SSH_MOUNT_DUMMY_GIT"
gocd_format_version = 10


def get_pipelines(images):
    pipelines = []
    for image, versions in images.items():
        for version, _ in versions.items():
            image_version_name = "{}-{}".format(image, version)
            pipelines.append(image_version_name)
    return pipelines


def get_common_environment(pipelines):
    common_environment = {
        "environments": {
            ENVIRONMENT: {
                "environment_variables": {
                    "GIT_USER": "{{SECRET:[github][username]}}",
                    "DOCKERHUB_USERNAME": "{{SECRET:[dockerhub][username]}}",
                    "DOCKERHUB_PASSWORD": "{{SECRET:[dockerhub][password]}}",
                },
                "pipelines": pipelines,
            }
        }
    }
    return common_environment


def get_common_pipeline():
    common_pipeline = {
        "group": GROUP,
        "label_template": "${COUNT}",
        "lock_behaviour": "none",
        "display_order": -1,
        "template": TEAMPLATE,
    }
    return common_pipeline


def get_common_materials():
    common_materials = {
        # this is the name of material
        # says about type of material and url at once
        "publish_docker_git": {
            "git": "https://github.com/rasmunk/publish-docker-scripts.git",
            "branch": "main",
            "username": "${GIT_USER}",
            "password": "{{SECRET:[github][access_token]}}",
            "destination": "publish-docker-scripts",
        },
    }
    return common_materials

def  get_image_materials(image, version):
    image_materials = {
        "ssh_mount_dummy_git": {
            "git": "https://github.com/rasmunk/docker-ssh-mount-dummy.git",
            "branch": branch,
            "destination": "{}-{}".format(image, version),
        },
    }
    return image_materials


def get_upstream_materials(name, pipeline, stage):
    upstream_materials = {
        "upstream_{}".format(name): {
            "pipeline": pipeline,
            "stage": stage,
        }
    }
    return upstream_materials


def get_materials(image, version, upstream_pipeline=None, stage=None):
    materials = {}
    common_materials = get_common_materials()
    image_materials = get_image_materials(image, version)
    materials.update(common_materials)
    materials.update(image_materials)
    if upstream_pipeline and stage:
        upstream_materials = get_upstream_materials(image, upstream_pipeline, stage)
        materials.update(upstream_materials)
    return materials


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=PACKAGE_NAME)
    parser.add_argument(
        "--architecture-name",
        default="architecture.yml",
        help="The name of the architecture file that is used to configure the images to be built",
    )
    parser.add_argument(
        "--config-name", default="1.gocd.yml", help="Name of the output gocd config"
    )
    parser.add_argument(
        "--branch", default="master", help="The branch that should be built"
    )
    parser.add_argument(
        "--makefile", default="Makefile", help="The makefile that defines the images"
    )
    parser.add_argument(
        "--generate-test-image", default=False,
        help="Whether the script should generate a test image as well, loads the Jinja Dockerfile template in --test-image-path"
    )
    parser.add_argument(
        "--test-image-path", default=os.path.join("res", "tests", "Dockerfile.test.j2"),
        help="The path to Jinja Dockerfile template that is used to generate test images"
    )
    args = parser.parse_args()

    architecture_name = args.architecture_name
    config_name = args.config_name
    branch = args.branch
    makefile = args.makefile
    # Test image parameters
    generate_test_image = args.generate_test_image
    test_image_path = args.test_image_path

    # Load the architecture file
    architecture_path = os.path.join(current_dir, architecture_name)
    architecture = load(architecture_path, handler=yaml, Loader=yaml.FullLoader)
    if not architecture:
        print("Failed to load the architecture file at: {}".format(architecture_path))
        exit(-1)

    owner = architecture.get("owner", None)
    if not owner:
        print("Failed to find architecture the owner in: {}".format(architecture_path))
        exit(-1)

    images = architecture.get("architecture", None)
    if not images:
        print("Failed to find the architecture in: {}".format(architecture_path))
        exit(-1)

    list_images= list(images.keys())
    num_images = len(list_images) - 1

    print()
    # Get all pipelines
    pipelines = get_pipelines(images)

    # GOCD environment
    common_environments = get_common_environment(pipelines)

    # Common GOCD pipeline params
    common_pipeline_attributes = get_common_pipeline()

    generated_config = {
        "format_version": gocd_format_version,
        **common_environments,
        "pipelines": {},
    }

    # Generate the image Dockerfiles
    for image, versions in images.items():
        for version, build_data in versions.items():
            parent = build_data.get("parent", None)
            if not parent:
                print("Missing required parent for image: {}".format(image))
                exit(-2)

            if "image" not in parent:
                print("Missing required parent attribute 'image': {}".format(image))
                exit(-2)

            if "tag" not in parent:
                print("Missing required parent attribute 'tag': {}".format(image))
                exit(-2)

            if "owner" not in parent:
                parent_image = "{}:{}".format(
                    parent["image"], parent["tag"]
                )
            else:
                parent_image = "{}/{}:{}".format(
                    parent["owner"], parent["image"], parent["tag"]
                )

            template_file = build_data.get("file", "{}/Dockerfile.j2".format(image))
            output_file = "{}/Dockerfile.{}".format(image, version)
            template_content = load(template_file)
            if not template_content:
                print("Could not find the template file: {}".format(template_file))
                exit(-3)

            template = Template(template_content)
            output_content = None
            template_parameters = {"parent": parent_image}

            extra_template_file = build_data.get("extra_template", None)
            if extra_template_file:
                extra_template = load(extra_template_file)
                template_parameters["extra_template"] = extra_template

                # Check for additional template files that should
                # be copied over.
                extra_template_files = build_data.get("extra_template_files", [])
                target_dir = os.path.join(current_dir, image)
                for extra_file_path in extra_template_files:
                    extra_file_name = extra_file_path.split("/")[-1]
                    success, msg = copy(
                        extra_file_path, os.path.join(target_dir, extra_file_name)
                    )
                    if not success:
                        print(msg)
                        exit(-4)

            build_parameters = build_data.get("parameters", None)
            if build_parameters:
                template_parameters.update(**build_parameters)

            # Format the jinja2 template
            output_content = template.render(**template_parameters)

            # Save rendered template to a file
            write(output_file, output_content)
            print("Generated the file: {}".format(output_file))

    if generate_test_image:
        # Generate the test Dockerfiles for the images
        for image, versions in images.items():
            for version, build_data in versions.items():
                test_image = "{}/{}:{}".format(owner, image, version)

                test_output_file = "{}/Dockerfile.{}.test".format(image, version)
                test_template_content = load(test_image_path)
                if not test_template_content:
                    print(
                        "Could not find test template file: {}".format(test_image_path)
                    )
                    exit(-4)

                template = Template(test_template_content)
                test_output_content = template.render(parent=test_image)
                # Save the rendered template to a file
                write(test_output_file, test_output_content)

    # Generate the GOCD build config
    for image, versions in images.items():
        for version, build_data in versions.items():
            parent = build_data.get("parent", None)
            if (
                parent
                and "pipeline_dependent" in parent
                and parent["pipeline_dependent"]
            ):
                parent_pipeline = "{}-{}".format(parent["image"], parent["tag"])
                materials = get_materials(
                    image,
                    version,
                    upstream_pipeline=parent_pipeline,
                    stage="push"
                )
            else:
                materials = get_materials(
                    image,
                    version
                )

            image_version_name = "{}-{}".format(image, version)
            image_pipeline = {
                **common_pipeline_attributes,
                "materials": materials,
                "parameters": {
                    "IMAGE": image,
                    "DEFAULT_TAG": version,
                    "SRC_DIRECTORY": "{}-{}".format(image, version),
                    "TEST_DIRECTORY": "{}-{}".format(image, version),
                    "PUSH_DIRECTORY": "publish-docker-scripts",
                    "COMMIT_TAG": COMMIT_TAG,
                    "ARGS": "",
                },
            }
            generated_config["pipelines"][image_version_name] = image_pipeline

    path = os.path.join(current_dir, config_name)
    if not write(path, generated_config, handler=yaml):
        print("Failed to save config")
        exit(-1)
    print("Generated a new GOCD config in: {}".format(path))

    # Update the Makefile such that it contains every image
    # image
    makefile_path = os.path.join(current_dir, makefile)
    makefile_content = load(makefile_path, readlines=True)
    new_makefile_content = []

    for line in makefile_content:
        if "ALL_IMAGES:=" in line:
            images_declaration = "ALL_IMAGES:="
            for image in images:
                images_declaration += "{} ".format(image)
            new_makefile_content.append(images_declaration)
            new_makefile_content.append("\n")
        else:
            new_makefile_content.append(line)

    # Write the new makefile content to the Makefile
    write(makefile_path, new_makefile_content)
    print("Generated a new Makefile in: {}".format(makefile_path))
