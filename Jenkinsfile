node {
  stage 'Unit test'
  sh 'echo pytest tests/'
  stage 'build'
  openshiftBuild(buildConfig: 'frontend', showBuildLogs: 'true')
  stage 'deploy'
  openshiftDeploy(deploymentConfig: 'frontend')
}
