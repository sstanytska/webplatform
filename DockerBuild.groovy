import hudson.EnvVars

//  This Jenkingfile will talk to Nexus grap existing version of application and assing as env.existVersion
//  Then will get git last release
//  If version does not matches Job will build the image and push to nexus

node {
  stage('poll') {
    // Poll last update of the default branch
    git credentialsId: 'git_account', url: 'https://github.com/fuchicorp/webplatform.git'
  }

  def app
  stage('Copy kube config') {

    // Copy config file to WORKSPACE if does not exist
    sh 'if [ -f config ]; then  :; else cp -rf /fuchicorp/config ${WORKSPACE} ; fi'
  }

  stage('New release GIT') {

    // Get latest release from local git
    env.release = sh returnStdout: true, script: 'git describe --abbrev=0 --tags'
  }

  stage('Get version existing version') {

    // Grab last pushed version docker images on nexus
    env.existVersion = sh returnStdout: true, script: 'sh bash/bin/getExistVersion.sh'
  }

  if ("${env.existVersion}" != "${env.release}") {

    stage('Build docker image') {

      // Build the image
        app = docker.build("fuchicorp")
    }

    stage('Push image') {

       // Push image to the Nexus with new release
        docker.withRegistry('http://nexus.fuchicorp.com:8085', 'docker-private-credentials') {
            app.push("${env.release}")
            app.push("latest")
        }
    }
  }
}
